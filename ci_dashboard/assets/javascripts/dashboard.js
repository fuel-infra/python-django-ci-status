$(function() {
    var AUTOREFRESH_COUNTDOWN = 5 * 60 * 1000,
        autoRefreshTimer;

    $('.ci-card-link').on('click', function(e) {
        e.preventDefault();
        $('a[aria-controls="' + $(this).data('tab') + '"]').click();
    });

    var processTab = function(newHash) {
        var hash = newHash || location.hash,
            hashPieces = hash.split('?'),
            activeTab = $('[href="' + hashPieces[0] + '"]');

        if (hash) {
            activeTab && activeTab.tab('show');
        }
    };

    // onready go to the tab requested in the page hash
    processTab();

    // when the nav item is selected update the page hash
    $('ul.nav-tabs a, ul.nav-pills a').on('shown.bs.tab', function(e) {
        var scrollmem = $('body').scrollTop();

        window.location.hash = e.target.hash;

        $('html,body').scrollTop(scrollmem);
    });


    var activateAutoRefresh = function(enable) {
        clearTimeout(autoRefreshTimer);

        if (enable) {
            autoRefreshTimer = setTimeout(function() {
                window.location.reload(true)
            }, AUTOREFRESH_COUNTDOWN);
        }
    };

    var _enableAutoRefresh = function(container) {
        container.removeClass('btn-default').addClass('btn-success active');
        $('span', container).text('Page Autorefresh: ON');

        activateAutoRefresh(true);
    };

    var _disableAutoRefresh = function(container) {
        container.removeClass('btn-success active').addClass('btn-default');
        $('span', container).text('Page Autorefresh: OFF');

        activateAutoRefresh(false);
    };

    if (location.pathname == '/dashboard/' &&
        'localStorage' in window &&
        window['localStorage'] !== null) {

        var toggle = $('#autorefresh-toggle'),
            container = toggle.parent(),
            initialValue = localStorage.getItem('ci_status.autorefresh') || 'false';

        if (initialValue == 'true') {
            toggle.prop('checked', true);
            _enableAutoRefresh(container);
        }

        toggle.on('change', function () {
            if (toggle.prop('checked')) {
                localStorage.setItem('ci_status.autorefresh', 'true');
                _enableAutoRefresh(container);
            } else {
                localStorage.setItem('ci_status.autorefresh', 'false');
                _disableAutoRefresh(container);
            }
        });
    }
});
