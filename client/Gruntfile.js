/* eslint no-console: 0 */

module.exports = function(grunt) {
  var fs = require('fs'),
      path = require('path'),
      superagent = require('superagent'),
      Gettext = require("node-gettext");

  var fileToDataURI = function(filepath) {
    try {
      var mimeMap = {
        'css': 'text/css',
        'ico': 'image/x-icon',
        'js': 'application/javascript',
        'png': 'image/png',
        'woff': 'application/woff'
      }

      var ext = filepath.split('.').pop();
      var mimetype = (ext in mimeMap) ? mimeMap[ext] : 'application/octet-stream';

      fs.accessSync(filepath, fs.F_OK);
      var filecontent = fs.readFileSync(filepath);

      return 'data:' + mimetype + ';charset=utf-8;base64,' + new Buffer(filecontent).toString('base64');
    } catch (e) {
      return filepath;
    }
  };

  grunt.initConfig({
    eslint: {
      src: [
        'Gruntfile.js',
        'app/js/**/*.js',
        '!app/js/lib/*.js',
        '!app/js/locale/*.js',
        '!app/js/crypto/lib/*.js',
        'tests/**/*.js'
      ]
    },

    clean: {
      all: ['tmp', 'build']
    },

    copy: {
      sources: {
        files: [
          { dest: 'app/css', cwd: '.', src: ['node_modules/bootstrap-inline-rtl/dist/css/bootstrap.css'], expand: true, flatten: true },
          { dest: 'app/css', cwd: '.', src: ['node_modules/ui-select/dist/select.min.css'], expand: true, flatten: true },
          { dest: 'app/fonts', cwd: '.', src: ['node_modules/bootstrap-inline-rtl/fonts/*'], expand: true, flatten: true },
          { dest: 'app/js/locale', cwd: '.', src: ['node_modules/angular-i18n/angular-locale*'], expand: true, flatten: true },
          { dest: 'app/js/lib/', cwd: '.', src: ['node_modules/stacktrace-js/dist/stacktrace.min.js'], expand: true, flatten: true },
          { dest: 'app/js/lib/', cwd: '.', src: ['node_modules/scrypt-async/scrypt-async.min.js'], expand: true, flatten: true },
          { dest: 'app/js/lib/', cwd: '.', src: ['node_modules/openpgp/dist/openpgp.min.js'], expand: true, flatten: true },
          { dest: 'app/js/lib/', cwd: '.', src: ['node_modules/angular/angular.min.js'], expand: true, flatten: true },
          { dest: 'app/js/lib/', cwd: '.', src: ['node_modules/angular-aria/angular-aria.min.js'], expand: true, flatten: true },
          { dest: 'app/js/lib/', cwd: '.', src: ['node_modules/angular-filter/dist/angular-filter.min.js'], expand: true, flatten: true },
          { dest: 'app/js/lib/', cwd: '.', src: ['node_modules/angular-resource/angular-resource.min.js'], expand: true, flatten: true },
          { dest: 'app/js/lib/', cwd: '.', src: ['node_modules/angular-route/angular-route.min.js'], expand: true, flatten: true },
          { dest: 'app/js/lib/', cwd: '.', src: ['node_modules/angular-sanitize/angular-sanitize.min.js'], expand: true, flatten: true },
          { dest: 'app/js/lib/', cwd: '.', src: ['node_modules/angular-translate/dist/angular-translate.min.js'], expand: true, flatten: true },
          { dest: 'app/js/lib/', cwd: '.', src: ['node_modules/angular-translate-loader-url/angular-translate-loader-url.min.js'], expand: true, flatten: true },
          { dest: 'app/js/lib/', cwd: '.', src: ['node_modules/angular-translate-loader-static-files/angular-translate-loader-static-files.min.js'], expand: true, flatten: true },
          { dest: 'app/js/lib/', cwd: '.', src: ['node_modules/angular-ui-bootstrap/dist/ui-bootstrap-tpls.js'], expand: true, flatten: true },
          { dest: 'app/js/lib/', cwd: '.', src: ['node_modules/d3/build/d3.min.js'], expand: true, flatten: true },
          { dest: 'app/js/lib/', cwd: '.', src: ['node_modules/file-saver/FileSaver.js'], expand: true, flatten: true },
          { dest: 'app/js/lib/', cwd: '.', src: ['node_modules/angular-file-saver/dist/angular-file-saver.min.js'], expand: true, flatten: true },
          { dest: 'app/js/lib/', cwd: '.', src: ['node_modules/@flowjs/flow.js/dist/flow.min.js'], expand: true, flatten: true },
          { dest: 'app/js/lib/', cwd: '.', src: ['node_modules/@flowjs/ng-flow/dist/ng-flow.min.js'], expand: true, flatten: true },
          { dest: 'app/js/lib/', cwd: '.', src: ['node_modules/zxcvbn/dist/zxcvbn.js'], expand: true, flatten: true },
          { dest: 'app/js/lib/', cwd: '.', src: ['node_modules/angular-zxcvbn/dist/angular-zxcvbn.js'], expand: true, flatten: true },
          { dest: 'app/js/lib/', cwd: '.', src: ['node_modules/angular-dynamic-locale/tmhDynamicLocale.min.js'], expand: true, flatten: true },
          { dest: 'app/js/lib/', cwd: '.', src: ['node_modules/ui-select/dist/select.min.js'], expand: true, flatten: true },
          { dest: 'app/js/crypto/lib/', cwd: '.', src: ['node_modules/openpgp/dist/openpgp.min.js'], expand: true, flatten: true },
          { dest: 'app/js/crypto/lib/', cwd: '.', src: ['node_modules/openpgp/dist/openpgp.worker.min.js'], expand: true, flatten: true },
          { dest: 'app/js/crypto/lib/', cwd: '.', src: ['node_modules/scrypt-async/scrypt-async.min.js'], expand: true, flatten: true }
        ]
      },
      build: {
        files: [{ dest: 'tmp/', cwd: 'app/', src: ['**'], expand: true }]
      },
      end2end_coverage: {
          files: [{
            dest: 'build/',
            cwd: 'app/',
            src: [
              '**',
              '!js/**/*.js', // Don't copy scripts that will be instrumented,
              'js/lib/*.js', // and copy scripts that should not be instrumented.
              'js/locale/*.js',
              'js/crypto/lib/*.js'
            ],
            expand: true
          }]
      }
    },

    useminPrepare: {
      html: [
        'tmp/index.html',
        'tmp/app.html'
      ],
      options: {
        staging: 'tmp',
        dest: 'tmp',
        flow: {
          steps: {
            js: ['concat'], // we avoid to minify intentionally! #1417 !
            css: ['concat']
          },
          post: {}
        }
      }
    },

    usemin: {
      html: [
        'tmp/index.html',
        'tmp/app.html',
        'tmp/views/**/*.html'
      ],
      options: {
        dirs: ['tmp']
      }
    },

    html: {
      files: ['**/*.html']
    },

    // Put all angular.js templates into a single file
    ngtemplates:  {
      GLClient: {
        cwd: 'app',
        options: {
          base: 'app/',
          quotes: 'single'
        },
        src: ['app.html', 'views/**/*.html'],
        dest: 'tmp/js/templates.js'
      }
    },

    mochaTest: {
      test: {
        options: {
          timeout: 30000,
          reporter: 'list',
        },
        src: ['tests/api/test.js'],
      },
    },

    'string-replace': {
      pass1: {
        files: {
          'tmp/index.html': 'tmp/index.html',
          'tmp/css/styles.css': 'tmp/css/styles.css',
          'tmp/js/scripts.js': 'tmp/js/scripts.js'
        },
        options: {
          replacements: [
            {
              pattern: '<script src="js/scripts.js"></script>',
              replacement: ''
            },
            {
              pattern: '<!-- start_globaleaks(); -->',
              replacement: 'start_globaleaks();'
            },
            {
              pattern: "src: url('../fonts/glyphicons-halflings-regular.eot');",
              replacement: ''
            },
            {
              pattern: "src: url('../fonts/glyphicons-halflings-regular.eot?#iefix') format('embedded-opentype'), url('../fonts/glyphicons-halflings-regular.woff2') format('woff2'), url('../fonts/glyphicons-halflings-regular.woff') format('woff'), url('../fonts/glyphicons-halflings-regular.ttf') format('truetype'), url('../fonts/glyphicons-halflings-regular.svg#glyphicons_halflingsregular') format('svg');",
              replacement: function () {
                return "src: url('" + fileToDataURI('tmp/fonts/glyphicons-halflings-regular.woff') + "') format('woff');";
              }
            },
            {
              pattern: /js\/locale\/([^\'\"\)]+)*/g,
              replacement: function (match) {
                return fileToDataURI('tmp/' + match);
              }
            },
            {
              pattern: /inlinefiles\/([^\'\"\)]+)*/g,
              replacement: function (match) {
                return fileToDataURI('tmp/' + match);
              }
            }
          ]
        }
      },
      pass2: {
        files: {
          'tmp/index.html': 'tmp/index.html'
        },
        options: {
          replacements: [
            {
              pattern: 'css/styles.css',
              replacement: function () {
                return fileToDataURI('tmp/css/styles.css');
              }
            }
          ]
        }
      },
      pass3: {
        files: {
          'tmp/js/crypto/scrypt-async.worker.js': 'tmp/js/crypto/scrypt-async.worker.js'
        },
        options: {
          replacements: [
            {
              pattern: 'scrypt-async.min.js',
              replacement: function () {
                return fileToDataURI('tmp/js/crypto/scrypt-async.min.js');
              }
            }
          ]
        }
      }
    },

    confirm: {
      'pushTranslationsSource': {
        options: {
          // Static text.
          question: 'WARNING:\n'+
                    'this task may cause translations loss and should be executed only on master branch.\n\n' +
                    'Are you sure you want to proceed (Y/N)?',
          input: '_key:y'
        }
      }
    },

    instrument: {
      files: 'js/**/*.js',
      options: {
        lazy: true,
        cwd: 'app/',
        basePath: 'build'
      }
    },

    protractor_coverage: {
      local: {
        options: {
          configFile: 'tests/end2end/protractor-coverage.config.js'
        }
      }
    },

    makeReport: {
      src: 'coverage/*.json',
      options: {
        type: 'lcov',
        dir: 'coverage',
        print: 'detail'
      }
    }
  });

  // Prefer explicit to loadNpmTasks to:
  //   require('matchdep').filterDev('grunt-*').forEach(grunt.loadNpmTasks);
  //
  // the reasons is during time strangely the automating loading was causing problems.
  grunt.loadNpmTasks('grunt-angular-templates');
  grunt.loadNpmTasks('grunt-confirm');
  grunt.loadNpmTasks('grunt-contrib-clean');
  grunt.loadNpmTasks('grunt-contrib-concat');
  grunt.loadNpmTasks('grunt-contrib-connect');
  grunt.loadNpmTasks('grunt-contrib-copy');
  grunt.loadNpmTasks('grunt-istanbul');
  grunt.loadNpmTasks('grunt-protractor-coverage');
  grunt.loadNpmTasks('grunt-string-replace');
  grunt.loadNpmTasks('grunt-usemin');
  grunt.loadNpmTasks('grunt-mocha-test');
  grunt.loadNpmTasks("gruntify-eslint");

  var readDynamicStrings = function() {
    var filecontent = grunt.file.read('app/data_src/dynamic_strings.json'),

    ret = {};
    ret['mapping'] = JSON.parse(filecontent);
    ret['inverse_mapping'] = {};
    for (var key in ret['mapping']) {
      ret['inverse_mapping'][(ret['mapping'][key])] = key;
    }

    return ret;
  };

  var readNoTranslateStrings = function() {
    return JSON.parse(grunt.file.read('app/data_src/notranslate_strings.json'));
  };

  var dynamic_strings = readDynamicStrings(),
      notranslate_strings = readNoTranslateStrings();

  grunt.registerTask('cleanupWorkingDirectory', function() {
    var x;
    var dirs;

    var rm_rf = function(dir) {
      var s = fs.statSync(dir);

      if (!s.isDirectory()) {return fs.unlinkSync(dir);}

      fs.readdirSync(dir).forEach(function(f) {
        rm_rf(path.join(dir || '', f || ''));
      });

      fs.rmdirSync(dir);
    };

    grunt.file.mkdir('build/');

    grunt.file.copy('tmp/index.html', 'build/index.html');
    grunt.file.copy('tmp/js/scripts.js', 'build/js/scripts.js');
    grunt.file.copy('tmp/js/plugin.js', 'build/js/plugin.js');

    grunt.file.mkdir('build/js/crypto/');
    grunt.file.copy('tmp/js/crypto/scrypt-async.worker.js', 'build/js/crypto/scrypt-async.worker.js');

    var copy_fun = function(absdir, rootdir, subdir, filename) {
      grunt.file.copy(absdir, path.join('build/' + dirs[x], subdir || '', filename || ''));
    };

    dirs = ['js/crypto/lib', 'l10n', 'data'];
    for (x in dirs) {
      grunt.file.recurse('tmp/' + dirs[x], copy_fun);
    }

    rm_rf('tmp');
  });

  function str_escape (val) {
      if (typeof(val) !== "string") {
        return val;
      }

      return val.replace(/[\n]/g, '\\n').replace(/[\t]/g, '\\r');
  }

  function str_unescape (val) {
      if (typeof(val) !== "string") {
        return val;
      }

      return val.replace(/\\n/g, '\n').replace(/\\t/g, '\t');
  }

  function readTransifexrc(){
    var transifexrc = fs.realpathSync(process.env.HOME + '/.transifexrc'),
      err = fs.stat(transifexrc),
      usernameRegexp = /username = (.*)/,
      passwordRegexp = /password = (.*)/,
      content, login = {};

    if (err) {
      console.log(transifexrc + " does not exist");
      console.log("It should contain");
      console.log("username = <your username>");
      console.log("password = <your password>");
      throw 'No transifexrc file';
    }

    content = grunt.file.read(transifexrc);
    login.username = usernameRegexp.exec(content)[1];
    login.password = passwordRegexp.exec(content)[1];
    return login;
  }

  var agent = superagent.agent(),
    baseurl = 'https://www.transifex.com/api/2/project/globaleaks',
    sourceFile = 'pot/en.po';

  function updateTxSource(cb){
    var url = baseurl + '/resource/master/content/',
      content = grunt.file.read(sourceFile),
      login = readTransifexrc();

    agent.put(url)
      .auth(login.username, login.password)
      .set('Content-Type', 'application/json')
      .send({'content': content})
      .end(function(err, res){
        if (res) {
          if (res.ok) {
            cb();
          } else {
           console.log('Error: ' + res.text);
          }
        } else {
          console.log('Error: failed to fetch resource ' + url);
        }
    });
  }

  function listLanguages(cb){
    var url = baseurl + '/resource/master/?details',
      login = readTransifexrc();

    agent.get(url)
      .auth(login.username, login.password)
      .end(function(err, res){
        if (res) {
          if (res.ok) {
            var result = JSON.parse(res.text);
            cb(result);
          } else {
            console.log('Error: ' + res.text);
          }
        } else {
          console.log('Error: failed to fetch resource');
        }
    });
  }

  function fetchTxTranslationsForLanguage(langCode, cb) {
    var resourceUrl = baseurl + '/resource/master/',
      login = readTransifexrc();

    var url = resourceUrl + 'stats/' + langCode + '/';

    agent.get(url)
      .auth(login.username, login.password)
      .end(function(err, res){
        if (res) {
          if (res.ok) {
            var content = JSON.parse(res.text);

            if (content.translated_entities > content.untranslated_entities) {
              var url = resourceUrl + 'translation/' + langCode + '/';
              agent.get(url)
                .auth(login.username, login.password)
                .end(function(err, res){
                  if (res) {
                    if (res.ok) {
                      cb(JSON.parse(res.text)['content']);
                    } else {
                      console.log('Error: ' + res.text);
                    }
                  } else {
                    console.log('Error: failed to fetch resource');
                  }
              });
            } else {
              cb();
            }
          } else {
            console.log('Error: ' + res.text);
          }
        } else {
          console.log('Error: failed to fetch resource');
        }
      });
  }

  function fetchTxTranslations(cb){
    var fetched_languages = 0,
      total_languages, supported_languages = {};

    listLanguages(function(result){
      result.available_languages = result.available_languages.sort(function(a, b) {
        if (a.code > b.code) {
          return 1;
        }

        if (a.code < b.code) {
          return -1;
        }

        return 0;
      });

      total_languages = result.available_languages.length;

      var fetchLanguage = function(language) {
        fetchTxTranslationsForLanguage(language.code, function(content){
          if (content) {
            var potFile = "pot/" + language.code + ".po";

            fs.writeFileSync(potFile, content);
            console.log("Fetched " + language.code);
            supported_languages[language.code] = language.name;
          }

          fetched_languages += 1;

          if (total_languages === fetched_languages) {
            var sorted_keys = Object.keys(supported_languages).sort();

            console.log("List of available translations:");

            for (var i in sorted_keys) {
              console.log(" { \"code\": \"" + sorted_keys[i] +
                          "\", \"name\": \"" + supported_languages[sorted_keys[i]] +"\" },");
            }

            cb(supported_languages);
          } else {
            fetchLanguage(result.available_languages[fetched_languages]);
          }
        });
      };

      fetchLanguage(result.available_languages[fetched_languages]);
    });
  }

  grunt.registerTask('makeTranslationsSource', function() {
    var gt = new Gettext(),
      translationStringRegexpHTML1 = /"(.+?)"\s+\|\s+translate/gi,
      translationStringRegexpHTML2 = /translate>(.+?)</gi,
      translationStringRegexpJSON = /"en": "(.+)"/gi,
      translationStringCount = 0;

    gt.addTextdomain("en");

    function addString(str) {
      if (notranslate_strings.indexOf(str) !== -1) {
        return;
      }

      if (str in dynamic_strings['mapping']) {
        str = dynamic_strings['mapping'][str];
        gt.setTranslation("en", "", str, str);
      } else {
        gt.setTranslation("en", "", str, str);
      }

      translationStringCount += 1;
    }

    function extractStringsFromHTMLFile(filepath) {
      var filecontent = grunt.file.read(filepath),
        result;

      result = translationStringRegexpHTML1.exec(filecontent);
      while (result) {
        addString(result[1]);
        result = translationStringRegexpHTML1.exec(filecontent);
      }

      result = translationStringRegexpHTML2.exec(filecontent);
      while (result) {
        addString(result[1]);
        result = translationStringRegexpHTML2.exec(filecontent);
      }

    }

    function extractStringsFromJSONFile(filepath) {
      var filecontent = grunt.file.read(filepath),
        result;

      result = translationStringRegexpJSON.exec(filecontent);
      while (result) {
        addString(result[1]);
        result = translationStringRegexpJSON.exec(filecontent);
      }
    }

    function extractStringsFromTXTFile(filepath) {
      var filecontent = grunt.file.read(filepath),
          lines = filecontent.split("\n");

      for (var i=0; i<lines.length; i++){
        // we skip adding empty strings and variable only strings
        if (lines[i] !== '' && !lines[i].match(/^%[a-zA-Z0-9]+%/g)) {
          addString(lines[i]);
        }
      }
    }

    function extractStringsFromFile(filepath) {
      var ext = filepath.split('.').pop();

      if (ext === 'html') {
        extractStringsFromHTMLFile(filepath);
      } else if (ext === 'json') {
        extractStringsFromJSONFile(filepath);
      } else if (ext === 'txt') {
        extractStringsFromTXTFile(filepath);
      }
    }

    function extractStringsFromDir(dir) {
      grunt.file.recurse(dir, function(absdir, rootdir, subdir, filename) {
        var filepath = path.join(dir, subdir || '', filename || '');
        extractStringsFromFile(filepath);
      });
    }

    extractStringsFromFile('app/app.html');
    extractStringsFromFile('app/translations.html');
    extractStringsFromFile('app/data_src/appdata.json');
    extractStringsFromFile('app/data_src/field_attrs.json');

    extractStringsFromDir('app/views');
    extractStringsFromDir('app/data_src/txt');
    extractStringsFromDir('app/data_src/fields');

    grunt.file.mkdir("pot");

    fs.writeFileSync("pot/en.po", gt.compilePO("en"));

    console.log("Written " + translationStringCount + " string to pot/en.po.");
  });

  grunt.registerTask('☠☠☠pushTranslationsSource☠☠☠', function() {
    var done = this.async();

    updateTxSource(done);
  });

  grunt.registerTask('fetchTranslations', function() {
    var done = this.async(),
      gt = new Gettext(),
      fileContents = fs.readFileSync("pot/en.po"),
      lang_code;

    function addTranslation(translations, key, value) {
      if (key in dynamic_strings['inverse_mapping']) {
        key = dynamic_strings['inverse_mapping'][key];
      }

      translations[key] = value;
    }

    fetchTxTranslations(function(supported_languages) {
      gt.addTextdomain("en", fileContents);
      var strings = gt.listKeys("en", "");

      for (lang_code in supported_languages) {
        var translations = {}, output;

        for (var i = 0; i < strings.length; i++) {
          var string = strings[i];
          gt.addTextdomain(lang_code, fs.readFileSync("pot/" + lang_code + ".po"));
          addTranslation(translations, string, str_unescape(gt.dgettext(lang_code, str_escape(string))));
        }

        output = JSON.stringify(translations);

        fs.writeFileSync("app/l10n/" + lang_code + ".json", output);
      }

      done();
    });
  });

  grunt.registerTask('makeAppData', function() {
    var done = this.async(),
      gt = new Gettext(),
      fileContents = fs.readFileSync("pot/en.po"),
      lang_code;

    fetchTxTranslations(function(supported_languages) {
      var json = JSON.parse(fs.readFileSync("app/data_src/appdata.json")),
          output = {},
          version = json['version'],
          default_questionnaire = json['default_questionnaire'],
          templates = json['templates'],
          templates_sources = {};

      var translate_object = function(object, keys) {
        for (var k in keys) {
          for (lang_code in supported_languages) {
            object[keys[k]][lang_code] = str_unescape(gt.dgettext(lang_code, str_escape(object[keys[k]]['en'])));
          }
        }
      };

      var translate_field = function(field) {
        var i;
        translate_object(field, ['label', 'description', 'hint', 'multi_entry_hint']);

        for (i in field['attrs']) {
          translate_object(field['attrs'][i], ['value']);
        }

        for (i in field['options']) {
          translate_object(field['options'][i], ['label']);
        }

        for (i in field['children']) {
          translate_field(field['children'][i]);
        }
      };

      var translate_step = function(step) {
        translate_object(step, ['label', 'description']);

        for (var c in step['children']) {
          translate_field(step['children'][c]);
        }
      };

      var translate_questionnaire = function(questionnaire) {
        for (var s in questionnaire) {
          translate_step(questionnaire[s]);
        }
      };

      gt.addTextdomain("en", fileContents);

      for (lang_code in supported_languages) {
        gt.addTextdomain(lang_code, fs.readFileSync("pot/" + lang_code + ".po"));
      }

      grunt.file.recurse('app/data_src/txt', function(absdir, rootdir, subdir, filename) {
        var template_name = filename.split('.txt')[0],
            filepath = path.join('app/data_src/txt', subdir || '', filename || '');

        templates_sources[template_name] = grunt.file.read(filepath);
      });

      for (lang_code in supported_languages) {
        for (var template_name in templates_sources) {
          /* Skip to add these templates cause we still miss the database of storing them */
          if (['admin_test_email_title', 'admin_test_email_template'].indexOf(template_name) !== -1) {
            continue;
          }

          if (!(template_name in templates)) {
            templates[template_name] = {};
          }

          var tmp = templates_sources[template_name];

          var lines = templates_sources[template_name].split("\n");

          for (var i=0; i<lines.length; i++){

            // we skip adding empty strings and variable only strings
            if (lines[i] !== '' && !lines[i].match(/^%[a-zA-Z0-9]+%/g)) {
              tmp = tmp.replace(lines[i], str_unescape(gt.dgettext(lang_code, str_escape(lines[i]))));
            }
          }

          templates[template_name][lang_code] = tmp;
        }
      }

      output['version'] = version;
      output['default_questionnaire'] = default_questionnaire;
      output['templates'] = templates;
      output['node'] = {};

      for (var k in json['node']) {
        output['node'][k] = {};
        for (lang_code in supported_languages) {
          output['node'][k][lang_code] = str_unescape(gt.dgettext(lang_code, str_escape(json['node'][k]['en'])));
        }
      }

      translate_questionnaire(output['default_questionnaire']['steps']);

      output = JSON.stringify(output);

      fs.writeFileSync("app/data/appdata.json", output);

      grunt.file.recurse('app/data_src/fields', function(absdir, rootdir, subdir, filename) {
        var srcpath = path.join('app/data_src/fields', subdir || '', filename || '');
        var dstpath = path.join('app/data/fields', subdir || '', filename || '');
        var field = JSON.parse(fs.readFileSync(srcpath));
        translate_field(field);
        field = JSON.stringify(field);
        fs.writeFileSync(dstpath, field);
      });

      grunt.file.copy('app/data_src/field_attrs.json', 'app/data/field_attrs.json');

      done();
    });

  });


  // Processes misc files included in the GlobaLeaks repository that need to be
  // included as data like the license and changelog
  grunt.registerTask('includeExternalFiles', function() {
      var content = grunt.file.read('../LICENSE');
      fs.writeFileSync('tmp/data/license.txt', content)

      content = grunt.file.read('../CHANGELOG');
      fs.writeFileSync('tmp/data/changelog.txt', content)
      var lines = content.split("\n"),
          changelog = [],
          obj;

      for (var i = 0; i < lines.length; i++) {
        var l = lines[i];
        // Format of the first line of every new release is:
        // Changes in version 2.76.4 - 2017-04-12
        if (/^(Changes in version)/.test(l)) {
          obj = {};
          // Matches version and date
          var res = l.match(/(\d+\.\d+(\.\d+)?) - (\d{4}-\d{2}-\d{2})/);
          obj.title = l;
          obj.version = res[1];
          obj.date = res[3];
          obj.txt = '';
          changelog.push(obj);
        } else {
          obj.txt += l + '\n';
        }
      }

      obj.txt = obj.txt.replace(/^\s+|\s+$/g, "");

      // Using object here due to issues with exporting raw lists via json
      var output = JSON.stringify({'v': changelog});
      fs.writeFileSync('tmp/data/changelog.json', output);

      console.log('Copied misc files into ./tmp');
  });


  // Run this task to push translations on transifex
  grunt.registerTask('pushTranslationsSource', ['confirm', '☠☠☠pushTranslationsSource☠☠☠']);

  // Run this task to fetch translations from transifex and create application files
  grunt.registerTask('updateTranslations', ['fetchTranslations', 'makeAppData']);
  // Run this to build your app. You should have run updateTranslations before you do so, if you have changed something in your translations.
  grunt.registerTask('build',
    ['clean', 'copy:sources', 'copy:build', 'includeExternalFiles', 'ngtemplates', 'useminPrepare', 'concat', 'usemin', 'string-replace', 'cleanupWorkingDirectory']);

  grunt.registerTask('generateCoverallsJson', function() {
    var done = this.async();
    var coveralls = require('coveralls');

    coveralls.getBaseOptions(function(err, options) {
      if (err) {
        grunt.log.error("Failed to get options, with error: " + err);
        return done(err);
      }

      var fileName = 'coverage/lcov.info';
      fs.readFile(fileName, 'utf8', function(err, fileContent) {
        if (err) {
          grunt.log.error("Failed to read file '" + fileName + "', with error: " + err);
          return done(err);
        }

        coveralls.convertLcovToCoveralls(fileContent, options, function(err, coverallsJson) {
          if (err) {
            grunt.log.error("Failed to convert '" + fileName + "' to coveralls: " + err);
            return done(err);
          }

          // fix file paths so submitting this info with the python coverage works correctly on coveralls.
          if (coverallsJson.source_files) {
            coverallsJson.source_files.forEach(function(srcfile) {
              srcfile.name = "../client/" + srcfile.name;
            });
          }

          var dstpath = 'coverage/coveralls.json';
          fs.writeFileSync(dstpath, JSON.stringify(coverallsJson));

          grunt.verbose.ok("Successfully converted " + fileName + " to coveralls json.");
          done();
        });
      });
    });
  });

  grunt.registerTask('end2end-coverage-instrument', [
    'clean',
    'copy:sources',
    'copy:end2end_coverage',
    'instrument'
  ]);

  grunt.registerTask('end2end-coverage-report', [
    'makeReport',
    'generateCoverallsJson'
  ]);
};
