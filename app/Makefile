all:  js css

js: ../pub/js/regist.min.js  
../pub/js/regist.min.js: regist.js
	uglifyjs --compress --mangle -- regist.js | sed 's/\x27/\&#39;/g' > ../pub/js/regist.min.js


css: regist.css
	cat regist.css  > ../pub/css/regist.css 

