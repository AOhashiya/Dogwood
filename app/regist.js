var getMonthDays = function(year, month) {
    return new Date(year, month, 0).getDate();
};
$(function() {
    $('#year_select').on("change",function(){
	var year  = $('#year_select').val();
	var month = $('#month_select').val();
        var day   = 0;
        $('#day_select option').remove();
	if (year != '' && month != '') {
	    day = getMonthDays(year, month);
	    for (var i = 1; i <= day; i++) {
		$('#day_select').append("<option value=" + Number(i) + ">" + i + "</option>");
	    }
	} else {
	    $('#day_select').append("<option value=''>-</option>");
	}
	return true;
    });
    $('#month_select').on("change",function(){
	var year  = $('#year_select').val();
	var month = $('#month_select').val();
        var day   = 0;
        $('#day_select option').remove();
	if (year != '' && month != '') {
	    day = getMonthDays(year, month);
	    for (var i = 1; i <= day; i++) {
		$('#day_select').append("<option value=" + Number(i) + ">" + i + "</option>");
	    }
	} else {
	    $('#day_select').append("<option value=''>-</option>");
	}
	return true;
    });
    $(".iframe_box").colorbox({
        iframe:true,
        innerWidth:600,   //幅の指定
        innerHeight:400 //高さの指定
    });
    $(".iframe_company_box").colorbox({
        iframe:true,
        innerWidth:600,   //幅の指定
        innerHeight:650 //高さの指定
    });
    $('.close').click(function () {
	parent.location.reload();
	parent.$.colorbox.close();
    });
    jQuery(document).on('cbox_closed', function(){
	parent.location.reload();
    });
    $(".policy_submit").click(function () {
	if ($("#policy").prop("checked") === false) {
	    alert("個人情報の同意にチェックを入れてください。");
	    return false;
	} else {
	    $('#entry_policy').submit();
	    return true;
	}
    });
    $('.entryConfirm').click(function() {
	$(this).parents('form').attr('action', $(this).data('action'));
	$(this).parents('form').submit();
    });
    $("#entrySubmit").click(function () {
	var lang_str = '';
	for(var i=1; i < 6; i++) {
	    var st = $('[name^=language_' + i + ']').val();
	    if(lang_str == '') {
		lang_str = st;
	    } else {
		if(st != '' && st != 0) {
		    lang_str = lang_str + ',' + st;
		}
	    }
	}
        $('[name=language]').val(lang_str);
    });
});


