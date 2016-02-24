$(function() {
    var timerCountdown = $('#countdown-timer'),
        lastUpdate = new Date(timerCountdown.text());

    var _timeToMinutes = function(lastUpdate) {
        var minutes = Math.floor((Date.now() - lastUpdate) / 60000),
            hours = 0;

        if (minutes > 60) {
            hours = Math.floor(minutes / 60);
            minutes = minutes % 60;
        }

        if (hours > 0) {
            return 'Updated ' + hours + ' hours and ' + minutes + ' mins ago';
        } else {
            return 'Updated ' + minutes + ' mins ago';
        }
    };

    timerCountdown.text(_timeToMinutes(lastUpdate));


    setInterval(function() {
        timerCountdown.text(_timeToMinutes(lastUpdate));
    }, 30000);

    $('[data-toggle="tooltip"]').tooltip({
        trigger: 'hover',
        delay: 500,
    });
});
