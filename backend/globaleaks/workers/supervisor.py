# -*- encoding: utf-8 -*-
import logging
import multiprocessing
import os

from sys import executable

from twisted.internet import defer, reactor

from globaleaks.models.config import PrivateFactory, load_tls_dict
from globaleaks.orm import transact
from globaleaks.utils import tls
from globaleaks.utils.utility import log, datetime_now, datetime_to_ISO8601
from globaleaks.workers.process import HTTPSProcProtocol


class ProcessSupervisor(object):
    """
    A supervisor for all subprocesses that the main globaleaks process can launch
    """

    # TODO One child process death every 5 minutes is acceptable. Four every minute
    # is excessive.
    MAX_MORTALITY_RATE = 4 # 0.2

    def __init__(self, net_sockets, proxy_ip, proxy_port):
        log.info("Starting process monitor")

        self.shutting_down = False

        self.start_time = datetime_now()
        self.tls_process_pool = []
        self.tls_process_state = {
            'deaths': 0,
            'last_death': datetime_now(),
            'target_proc_num': multiprocessing.cpu_count(),
        }

        self.worker_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'https_worker.py')

        self.tls_cfg = {
          'proxy_ip': proxy_ip,
          'proxy_port': proxy_port,
          'debug': log.loglevel <= logging.DEBUG,
        }

        if len(net_sockets) == 0:
            log.err("No ports to bind to! Spawning processes will not work!")

        self.tls_cfg['tls_socket_fds'] = [ns.fileno() for ns in net_sockets]


    @transact
    def maybe_launch_https_workers(self, store):
        self.db_maybe_launch_https_workers(store)

    @defer.inlineCallbacks
    def db_maybe_launch_https_workers(self, store):
        privFact = PrivateFactory(store)

        on = privFact.get_val('https_enabled')
        if not on:
            log.info("Not launching workers")
            yield defer.succeed(None)
            return

        db_cfg = load_tls_dict(store)
        self.tls_cfg.update(db_cfg)

        chnv = tls.ChainValidator()
        ok, err = chnv.validate(db_cfg, must_be_disabled=False)

        if ok and err is None:
            log.info("Decided to launch https workers")
            yield self.launch_https_workers()
        else:
            log.info("Not launching https workers due to %s" % err)
            yield defer.fail(err)

    def launch_https_workers(self):
        self.tls_process_state['deaths'] = 0
        self.tls_process_state['last_death'] = datetime_now()

        d_lst = []
        for i in range(self.tls_process_state['target_proc_num']):
            d_lst.append(self.launch_worker())
        d = defer.DeferredList(d_lst)
        return d

    def launch_worker(self):
        pp = HTTPSProcProtocol(self, self.tls_cfg)
        reactor.spawnProcess(pp, executable, [executable, self.worker_path], childFDs=pp.fd_map, env=os.environ)
        self.tls_process_pool.append(pp)
        log.info('Launched: %s' % pp)
        return pp.startup_promise

    def handle_worker_death(self, pp, reason):
        """
        handle_worker_death accounts the worker's death and creates a new process
        in its place if the reason for death is reasonable and we haven't
        restarted the child an unreasonable number of times.
        """
        log.debug("Subprocess: %s exited with: %s" % (pp, reason))
        mortatility_rate = self.account_death()
        self.tls_process_pool.pop(self.tls_process_pool.index(pp))
        del pp

        if self.should_spawn_child(mortatility_rate):
            log.debug('Decided to respawn a child')
            self.launch_worker()
        elif self.last_one_out():
            self.shutting_down = False
            self.shutdown_d.callback(None)
            self.shutdown_d = None
            log.info("Supervisor has turned off all children")
        else:
            log.err("Not relaunching child process")

    def should_spawn_child(self, mort_rate):
        # TODO add logging based on condition hit

        if self.shutting_down:
            return False

        nrml_deaths = 3*self.tls_process_state['target_proc_num']

        # TODO hitting this condition means something is really wrong. Log it.
        max_deaths = nrml_deaths*150

        num_deaths = self.tls_process_state['deaths']

        return len(self.tls_process_pool) < self.tls_process_state['target_proc_num'] and \
               num_deaths < max_deaths and \
               (mort_rate < self.MAX_MORTALITY_RATE or num_deaths < nrml_deaths)

    def last_one_out(self):
        """
        last_one_out captures the condition of the last shutdown process before
        the process supervisor has closed all children.
        """
        return self.shutting_down and len(self.tls_process_pool) == 0

    def calc_mort_rate(self):
        d = self.tls_process_state['deaths']
        window = (datetime_now() - self.start_time).total_seconds()
        r = d / (window / 60.0) # deaths per minute
        return r

    def account_death(self):
        self.tls_process_state['deaths'] += 1
        r = self.calc_mort_rate()
        log.debug('process death accountant: r=%3f, d=%2f'  % (r, self.tls_process_state['deaths']))
        return r

    def is_running(self):
        return len(self.tls_process_pool) > 0

    def get_status(self):
        s = {
            'msg': '',
            'timestamp': datetime_to_ISO8601(datetime_now()),
            'type': 'info'
        }

        r = self.calc_mort_rate()

        if self.is_running():
            if r == 0:
                m = "Everything is running normally."
            else:
                m = "The supervisor has a mortality rate of r=%1.2f deaths/minute" % r
        elif not self.should_spawn_child(r):
            m = "The supervisor will not create new workers"
        else:
            m = "Nothing is being served"

        s['msg'] = m

        return s

    def shutdown(self):
        log.debug('Starting shutdown of %d children' % len(self.tls_process_pool))

        # Handle condition where shutdown is called with no active children
        if not self.is_running():
            return defer.succeed(None)

        self.shutdown_d = defer.Deferred()
        self.shutting_down = True

        for pp in self.tls_process_pool:
            try:
                pp.transport.signalProcess('KILL')
            except OSError as e:
                log.debug('Tried to signal: %d got: %s' % (pp.transport.pid, e))

        return self.shutdown_d
