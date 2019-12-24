/* =========================================================*/
// jquery.smoothscroll.js / ver.1.4

// Copyright (c) 2018 CoolWebWindow
// This code is released under the MIT License
// https://osdn.jp/projects/opensource/wiki/licenses%2FMIT_license

// Date: 2018-08-14
// Author: CoolWebWindow
// Mail: info@coolwebwindow.com
// Web: http://www.coolwebwindow.com

// Used jquery.js
// http://jquery.com/
/* =========================================================*/

$(function($){
	$.fn.smoothscroll = function(config) {
		// オプション
		var o = $.extend({
			easing      : 'swing', // 動作パターン
			speed       : 500,     // スクロールの速度
			margintop   : 0,       // スクロール位置の変更
			headerfix   : '',      // 固定されているヘッダーのセレクタ
			outersmooth : true     // 他ページからの内部リンクをスムーススクロールさせる
		}, config);

		// ページ外リンク
		var urlHash = location.hash;
		// スムーススクロールあり
		if(o.outersmooth){
			if(urlHash) {
				$('html,body').stop().animate({scrollTop:0}, '1');
				setTimeout(function(){
					// 移動先を取得
					var target = $(urlHash);
					// 移動先を数値で取得
					if(o.headerfix != ''){
						var navHeight = o.headerfix.outerHeight(true);
						var position = target.offset().top - navHeight - o.margintop;
					} else {
						var position = target.offset().top - o.margintop;
					}
					// スムーススクロール
					$('html,body').stop().animate({scrollTop:position}, o.speed, o.easing);
				}, 100);
			}
		// スムーススクロールなし
		} else {
			if(urlHash) {
				setTimeout(function(){
					// 移動先を取得
					var target = $(urlHash);
					// 移動先を数値で取得
					if(o.headerfix != ''){
						var navHeight = o.headerfix.outerHeight(true);
						var position = target.offset().top - navHeight - o.margintop;
					} else {
						var position = target.offset().top - o.margintop;
					}
					// 移動
					$('html,body').scrollTop(position);
				}, 100);
			}
		}

		// ページ内リンク
		$('a[href^="#"]').click(function() {
			// アンカーの値取得
			var href= $(this).attr("href");
			// 移動先を取得
			var target = $(href == '#' || href == '' ? 'html' : href);
			// 移動先を数値で取得
			if(o.headerfix != ''){
				var navHeight = o.headerfix.outerHeight(true);
				var position = target.offset().top - navHeight - o.margintop;
			} else {
				var position = target.offset().top - o.margintop;
			}
			// スムーススクロール
			$('html,body').stop().animate({scrollTop:position}, o.speed, o.easing);
		});
	};
});

