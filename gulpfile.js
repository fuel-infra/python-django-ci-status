var gulp = require('gulp');
var sass = require('gulp-sass');
var watch = require('gulp-watch');
var minifycss = require('gulp-minify-css');
var rename = require('gulp-rename');
var livereload = require('gulp-livereload');
var uglify = require('gulp-uglify');
var concat = require('gulp-concat');
var autoprefixer = require('gulp-autoprefixer');

var sassFolders = [
    'ci_dashboard/assets/scss/*.scss'
];
var stylesheetsPath = 'ci_dashboard/static/ci_dashboard/stylesheets';

/* Compile and minify Sass */
gulp.task('sass', function() {
    return gulp.src(sassFolders)
        .pipe(sass())
        .pipe(autoprefixer({
            browsers: ['last 2 versions'],
            cascade: false
        }))
        .pipe(concat('application.css'))
        .pipe(gulp.dest(stylesheetsPath))
        .pipe(rename({suffix: '.min'}))
        .pipe(minifycss())
        .pipe(gulp.dest(stylesheetsPath))
        .pipe(livereload());
});

var BOOTSTRAP = [
    'bower_components/bootstrap-sass/assets/javascripts/bootstrap.min.js',
];

var jsFolders = [
    'bower_components/jquery/dist/jquery.min.js',
    'ci_dashboard/assets/javascripts/*.js'
];
var jsPath = 'ci_dashboard/static/ci_dashboard/javascripts'

gulp.task('js', ['js:bootstrap', 'js:deps']);

gulp.task('js:bootstrap', function() {
    return gulp.src(BOOTSTRAP)
        .pipe(concat('bootstrap.js'))
        .pipe(gulp.dest(jsPath))
        .pipe(rename({suffix: '.min'}))
        .pipe(uglify())
        .pipe(gulp.dest(jsPath))
});

gulp.task('js:deps', function() {
    return gulp.src(jsFolders)
        .pipe(concat('application.js'))
        .pipe(gulp.dest(jsPath))
        .pipe(rename({suffix: '.min'}))
        .pipe(uglify())
        .pipe(gulp.dest(jsPath))
        .pipe(livereload());
});

var templatesFolders = [
    '**/templates/**'
];

/* Watch Files For Changes */
gulp.task('watch', function() {
    livereload.listen();
    gulp.watch(sassFolders, ['sass']);
    gulp.watch(jsFolders, ['js:deps']);

    /* Trigger a live reload on any Django template changes */
    gulp.watch(templatesFolders).on('change', livereload.changed);

});


gulp.task('build_static', ['sass', 'js']);
gulp.task('default', ['build_static', 'watch']);
