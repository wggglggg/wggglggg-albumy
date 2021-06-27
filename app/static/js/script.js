$(function () {
    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader('X-CSRFToken', csrf_token);
            }
        }
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
                },
                error: function (error) {
                    toast('Server error, please try again later.')
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
            }, 100);
        }
    }



    var flash = null;
    function toast(body) {
        clearTimeout(flash);
        var $toast = $('#toast');
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
            },
            error: function(error) {
                toast('Server error, please try again later.');
            }
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
           },
            error: function (error) {
               toast('Server error, please try again later.');
            }
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
            },
            error: function (error) {
                toast('Server error, please try again later.');
            }
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
            },
            error: function (error) {
                toast('Server error, please try again later.');
            }
        });
    }

});























