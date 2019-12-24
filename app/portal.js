/* ===================================================================

 * PC/スマホ向けメニュー切り替え

=================================================================== */
$(function($){
	var timer = false;
	var windowWidth = window.innerWidth || document.documentElement.clientWidth || 0;
	var nowWidth;

	// 読み込み時処理
	$(window).on('load', function(){
		spMenu();
		subNav();
		innerLink();
	});

	// リサイズ時処理
	$(window).on('resize', function(){
		if (timer !== false) {
			clearTimeout(timer);
		}
		timer = setTimeout(function() {
			nowWidth = window.innerWidth || document.documentElement.clientWidth || 0;
			if ( windowWidth != nowWidth ) {
				subNav();
				windowWidth = window.innerWidth || document.documentElement.clientWidth || 0;
			}
		}, 200);
	});

	// メニューボタンの表示（
	function spMenu() {
		$('#spMenu').on('click', function(e) {
			$('.gnav').slideToggle(e);
			$('#navBtnIcon').toggleClass('close');
			$('html, body').toggleClass('lock');
		});
	}

	// サブメニューの表示
	function subNav() {
		if ($('#spMenu').css('display') == 'block') {
			$('.subnav > a').off().on('click', function(e) {
				e.preventDefault();
				$(this).next('ul').slideToggle();
				$(this).parent().toggleClass('active');
			});
		} else {
			if('ontouchstart' in document) {
				$('.subnav > a').off().on('click', function(e) {
					e.preventDefault();
				});
			}
		}
	}

	// 内部リンク時のメニュー閉じ
	function innerLink() {
		if ($('#spMenu').css('display') == 'block') {
			$('.gnav a[href^="#"]').on('click', function(e) {
				$('.gnav').slideToggle(e);
				$('#navBtnIcon').toggleClass('close');
				$('html, body').toggleClass('lock');
			});
		}
	}

});



	// 検索窓




function searchToggle(obj, evt){
    var container = $(obj).closest('.search-wrapper');
        if(!container.hasClass('active')){
            container.addClass('active');
            evt.preventDefault();
        }
        else if(container.hasClass('active') && $(obj).closest('.input-holder').length == 0){
            container.removeClass('active');
            // clear input
            container.find('.search-input').val('');
        }
}
