module.exports = (grunt) ->
  grunt.initConfig
    pkg: grunt.file.readJSON("package.json")
    sass:
      options:
        style: "expanded"

      dist:
        files: [
          expand: true
          cwd: "../dev/sass"
          src: ["*.sass"]
          dest: "../app/static/css"
          ext: ".css"
        ]

    coffee:
      options:
        bare: true

      dist:
        files: [
          expand: true
          cwd: "../dev/coffee"
          src: ["*.coffee"]
          dest: "../app/static/js"
          ext: ".js"
        ]

    watch:
      options:
        livereload: false

      css:
        files: "../dev/sass/*.sass"
        tasks: ["sass"]

      js:
        files: "../dev/coffee/*.coffee"
        tasks: ["coffee"]

  grunt.loadNpmTasks "grunt-contrib-sass"
  grunt.loadNpmTasks "grunt-contrib-coffee"
  grunt.loadNpmTasks "grunt-contrib-watch"
  grunt.registerTask "default", [
    "sass"
    "coffee"
    "watch"
  ]
  return