$(function () {
    var default_error_message = 'Server error, please, try again later.';

    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader('X-CSRFToken', csrf_token);
            }
        }
    });

    $(document).ajaxError(function (event, request, settings) {
        var message = null;
        if (request.responseJSON && request.responseJSON.hasOwnProperty('message')) {
            message = request.responseJSON.message;
        } else if (request.responseText) {
            var IS_JSON = true;
            try{
                var data = JSON.parse(request.responseText);
            }
            catch(err) {
                IS_JSON = false;
            }
            if (IS_JSON && data !== undefined && data.hasOwnProperty('message')) {
                message = JSON.parse(request.responseText).message;
            } else {
                message = default_error_message;
            }
        } else {
            message = default_error_message;
        }
        toast(message, 'error');
        });


    // hide or show tag edit form
    $('#tag-btn').click(function () {
        $('#tags').hide();
        $('#tag-form').show();
    });
    $('#cancel-tag').click(function () {
        $('#tag-form').hide();
        $('#tags').show();
    });
    // hide or show description edit form
    $('#description-btn').click(function () {
        $('#description').hide();
        $('#description-form').show();
    });
    $('#cancel-description').click(function () {
        $('#description-form').hide();
        $('#description').show();
    });
    // delete confirm modal
    $('#confirm-delete').on('show.bs.modal', function (e) {
        $('.delete-form').attr('action', $(e.relatedTarget).data('href'));
    });

    $("[data-toggle='tooltip']").tooltip({title: moment($(this).data('timestamp')).format('lll')
    });

    if (is_authenticated) {
        setInterval(update_notification_count, 30000);
    }


    var hover_timer = null;

    function show_profile_popover(e) {
        var $el = $(e.target);
        // onPopoverEle = true;

        hover_timer = setTimeout(function () {
            hover_timer = null;
            $.ajax({
                type: 'GET',
                url: $el.data('href'),
                success: function (data) {
                    $el.popover({
                        html: true,
                        content: data,
                        trigger: 'manual',
                        animation: false
                    });
                    $el.popover('show');
                    $('.popover').on('mouseleave', function () {
                        setTimeout(function () {
                            $el.popover('hide');
                            //这里需要销毁这个pop over，否则实际中会无法实时更新关注状态
                            // $el.popover('dispose');
                        }, 200);
                    });
                }
            });
        }, 500)
    }

    var hover_time = null;
    function hide_profile_popover(e) {
        var $el = $(e.target);

        if (hover_time) {
            clearTimeout(hover_time);
            hover_time = null;
        } else {
            setTimeout(function () {
                if (!$('.popover:hover').length) {
                    $el.popover('hide');
                }
            }, 200);
        }
    }



    var flash = null;
    function toast(body, category) {
        clearTimeout(flash);
        var $toast = $('#toast');
        if (category === 'error') {
            $toast.css('background-color', 'red')
        } else {
            $toast.css('background-color', '#333')
        }
        $toast.text(body).fadeIn();
        flash = setTimeout(function () {
            $toast.fadeOut();
        }, 3000)
    }

    function update_followers_count(id) {
        var $el = $('#followers-count-' + id);
        $.ajax({
            type: 'GET',
            url: $el.data('href'),
            success: function (data) {
                $el.text(data.count);     //更新数字
            }
        //     error: function(error) {
        //         toast('Server error, please try again later.');
        //     }
        });
    }

    function follow(e) {
        var $el = $(e.target);
        var id = $el.data('id');

        $.ajax({
           type: 'POST',
           url: $el.data('href'),
           success: function (data) {
              $el.prev().show();
              $el.hide();
              update_followers_count(id);
              toast(data.message);
           }
            // error: function (error) {
            //    toast('Server error, please try again later.');
            // }
        });
    }

    function unfollow(e) {
        var $el = $(e.target);
        var id = $el.data('id');

        $.ajax({
            type: 'POST',
            url: $el.data('href'),
            success: function (data) {
                $el.next().show();
                $el.hide();
                update_followers_count(id);
                toast(data.message);
            }
            // error: function (error) {
            //     toast('Server error, please try again later.');
            // }
        });
    }


    $('.profile-popover').hover(show_profile_popover.bind(this), hide_profile_popover.bind(this));
    $(document).on('click', '.follow-btn', follow.bind(this));
    $(document).on('click', '.unfollow-btn', unfollow.bind(this));

    function update_followers_count(id) {
        var $el = $('#followers-count-' + id);
        $.ajax({
            type: 'GET',
            url: $el.data('href'),
            success: function (data) {
              $el.text(data.count);
            }
            // error: function (error) {
            //     toast(data.message);
            // }
        });
    }

    function update_notification_count() {
        var $el = $('#notification_badge');
        $.ajax({
            type: 'GET',
            url: $el.data('href'),
            success: function (data) {
                if (data.count == 0) {
                    $('#notification_badge').hide();
                } else {
                    $el.show();
                    $el.text(data.count)
                }
            }
        });
    }

});























