// Louis Vuitton
var _inside = _inside || [];
// var _inside = [];
var _insideLoaded = _insideLoaded || false;
var _insideJQ = _insideJQ || null;
window._insideViewUpdate = window._insideViewUpdate || function () { };

(function () {
	if (_insideLoaded) {
		window._insideViewUpdate();
		return;
	}
	_insideLoaded = true;

	var insideAccountKey = "IN-1011002";
	var insideTrackerURL = "cdn7.eu.inside.chat";
	var subsiteId = null;
	var insideOrderTotal = insideOrderTotal || 0;
	var _insideMaxLoop = 250;
	var _insideCurLoop = 0;
	var _insideFirstLoad = false;
	var _insideCurrency = null;
	var _insideCurUrl = window.location.href;
	var _insideCurPageType = "other";
	var _insideDataLayerIndex = 0;
	var _insideProdUrl = "";
	var _insideEventLabelTest = "";
	var _insideAddToCart = null;

	// Utility Functions
	function log() {
		if (typeof (console) != "undefined" && typeof (console.log) != "undefined") {
			// console.log("[INSIDE]", Array.prototype.slice.call(arguments));
		}
	}

	var hashJoaat = function (b) { for (var a = 0, c = b.length; c--;)a += b.charCodeAt(c), a += a << 10, a ^= a >> 6; a += a << 3; a ^= a >> 11; return ((a + (a << 15) & 4294967295) >>> 0).toString(16) };

	function debounce(func, delay) {
		let timeoutId;

		return function (...args) {
			const context = this;
			clearTimeout(timeoutId);
			timeoutId = setTimeout(() => {
				func.apply(context, args);
			}, delay);
		};
	}

	function deferWait(callback, test) {
		if (test()) {
			callback();
			return;
		}
		var _interval = 10;
		var _spin = function () {
			if (test()) {
				callback();
			}
			else {
				_interval = _interval >= 1000 ? 1000 : _interval * 2;
				setTimeout(_spin, _interval);
			}
		};
		setTimeout(_spin, _interval);
	}

	function keepWait(callback, test) {
		if (test()) {
			callback();
			if (_insideCurLoop >= _insideMaxLoop) {
				return;
			}
		}
		var _interval = 2000;
		var _spin = function () {
			if (test()) {
				_insideCurLoop = _insideCurLoop + 1;
				callback();
				if (_insideCurLoop >= _insideMaxLoop) {
					return;
				}
			}
			setTimeout(_spin, _interval);
		};
		setTimeout(_spin, _interval);
	}

	var indexOf = [].indexOf || function (prop) {
		for (var i = 0; i < this.length; i++) {
			if (this[i] === prop)
				return i;
		}
		return -1;
	};

	function myTrim(text) {
		try {
			if (typeof (text) != "undefined" && text != null)
				return typeof (text.trim) === "function" ? text.trim() : text.replace(/^\s+|\s+$/gm, '');
		} catch (trimex) { }

		return text;
	}

	function isNumeric(n) {
		try {
			return !isNaN(parseFloat(n)) && isFinite(n);
		}
		catch (tempex) {
		}

		return false;
	}

	function validateEmail(tempmail) {
		try {
			if (/^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$/.test(tempmail)) {
				return (true);
			}
		} catch (tempex) { }
		return (false);
	}

	function setCookie(cname, cvalue, exdays) {
		var hostName = window.location.hostname;
		var siteNameFragments = hostName.split(".");
		var siteName = siteNameFragments[1];
		var domain = siteNameFragments.slice(1, siteNameFragments.length).join(".");

		var d = new Date();
		d.setTime(d.getTime() + (exdays * 24 * 60 * 60 * 1000));
		var expires = "expires=" + d.toGMTString();
		document.cookie = cname + "=" + cvalue + "; " + expires + ";path=/" + ";domain=." + domain;
	}

	function getCookie(cname) {
		var name = cname + "=";
		var ca = document.cookie.split(';');
		for (var i = 0; i < ca.length; i++) {
			var c = myTrim(ca[i]);
			if (c.indexOf(name) == 0)
				return c.substring(name.length, c.length);
		}
		return null;
	}

	function deleteCookie(cname) {
		document.cookie = cname + "=" + 0 + "; " + "expires=01 Jan 1970 00:00:00 GMT" + ";path=/";
	}

	function roundToTwo(num) {
		if (Math != "undefined" && Math.round != "undefined")
			return +(Math.round(num + "e+2") + "e-2");
		else
			return num;
	}

	function getSearchParameters() {
		var prmstr = window.location.search.substring(1);
		return prmstr != null && prmstr != "" ? transformToAssocArray(prmstr) : [];
	}

	function transformToAssocArray(prmstr) {
		var params = [];
		var prmarr = prmstr.split("&");
		for (var i = 0; i < prmarr.length; i++) {
			params[i] = prmarr[i];
		}

		return params;
	}

	function randomIntFromInterval(min, max) {
		try {
			return Math.floor(Math.random() * (max - min + 1) + min);
		}
		catch (tempex) {
		}

		return min;
	}

	function getDecimalSign(number) {
		try {
			var tempnum = myTrim(number);

			if (tempnum.length > 3) {
				return tempnum.charAt(tempnum.length - 3);
			}
		}
		catch (signex) {
		}

		return ".";
	}

	// End of utility functions

	function processInside(tracker) {
		var searchUrl = "?search";
		var searchQueryString = null;
		var productCategoryUrl = null;
		var productCategoryQueryString = null;
		var productUrl = null;
		var productQueryString = null;
		var checkoutUrl = "/cart|/checkout";
		var checkoutQueryString = null;
		var orderConfirmedUrl = null;
		var orderConfirmedQueryString = null;

		function getViewData() {
			try {

				// Output view data
				// Default view data is "unknown"

				var insidedata = {};

				insidedata.action = "trackView";
				insidedata.type = "article";
				insidedata.url = window.location.href;
				insidedata.name = "Unknown Page: " + window.location.href;
				var tempurl = window.location.href.toLowerCase();

				var temppath = window.location.pathname;
				var temp_loc = temppath.split("/");
				var page = "";

				var add_tags = [];
				var params = getSearchParameters();
				var searchterm = "Search"; // Find the searchterm the
				// visitor
				// entered for the search page to be
				// used as the page name
				if (params != null && params.length > 0) {
					for (var i = 0; i < params.length; i++) {
						if (params[i].indexOf("q=") == 0) {
							searchterm = params[i].split("q=")[1];
						}
					}
				}

				for (var i = 1; i < temp_loc.length; i++) {
					if (temp_loc[i] != null && temp_loc[i].length > 0) {
						if (temp_loc[i].indexOf("?") != -1) {
							var temploc = temp_loc[i].split("?")[0];
							if (temploc.length > 0)
								page = temp_loc[i];
						}
						else {
							page = temp_loc[i];
						}
					}
				}
				var curpage = page.split("?")[0];
				insidedata.name = curpage;

				// Identify and assign the correct page type here
				// The part below is actually very flexible, can use
				// dataLayer too
				// sometimes, etc so if needed can also just delete the
				// global
				// variable parts and make your own algorithm. From my
				// experience
				// the following part will rarely work for all websites.

				var temppagetype = "other";
				try {
					if (typeof (window.utag_data) != "undefined" && window.utag_data != null && window.utag_data.pageType) {
						temppagetype = utag_data.pageType.toLowerCase();
					}
				} catch (tempex) { }

				if ((temppath == "/" || curpage == "index.html") && temp_loc.length < 3) {
					insidedata.type = "homepage";
				}
				else if (temppagetype == "homepage") {
					insidedata.type = "homepage";
				}
				else if (temppagetype == "search_result_list") {
					insidedata.type = "search";
				}
				else if (temppagetype == "product_list") {
					insidedata.type = "productcategory";
				}
				else if (temppagetype == "productsheet") {
					insidedata.type = "product";
				}
				else if (tempurl.indexOf("/login") != -1 || tempurl.indexOf("/registration") != -1) {
					insidedata.type = "login";
				}

				if (productCategoryUrl != null) {
					if (tempurl.indexOf(productCategoryUrl.toLowerCase()) > -1) {
						insidedata.type = "productcategory";
					}
				}
				if (productCategoryQueryString != null) {
					var tempelem = _insideJQ(productCategoryQueryString);
					if (tempelem != null && tempelem.length > 0) {
						insidedata.type = "productcategory";
					}
				}

				if (searchUrl != null) {
					if (tempurl.indexOf(searchUrl.toLowerCase()) > -1) {
						insidedata.type = "search";
					}
				}
				if (searchQueryString != null) {
					var tempelem = _insideJQ(searchQueryString);
					if (tempelem != null && tempelem.length > 0) {
						insidedata.type = "search";
					}
				}

				if (productUrl != null) {
					if (tempurl.indexOf(productUrl.toLowerCase()) > -1) {
						insidedata.type = "product";
					}
				}
				if (productQueryString != null) {
					var tempelem = _insideJQ(productQueryString);
					if (tempelem != null && tempelem.length > 0) {
						insidedata.type = "product";
					}
				}

				if (checkoutUrl != null) {
					if (tempurl.search(checkoutUrl.toLowerCase()) > 0) {
						insidedata.type = "checkout";
					}
				}
				if (checkoutQueryString != null) {
					var tempelem = _insideJQ(checkoutQueryString);
					if (tempelem != null && tempelem.length > 0) {
						insidedata.type = "checkout";
					}
				}

				if (orderConfirmedUrl != null) {
					if (tempurl.indexOf(orderConfirmedUrl.toLowerCase()) > -1) {
						insidedata.type = "orderconfirmed";
					}
				}
				if (orderConfirmedQueryString != null) {
					var tempelem = _insideJQ(orderConfirmedQueryString);
					if (tempelem != null && tempelem.length > 0) {
						insidedata.type = "orderconfirmed";
					}
				}

				try {
					if (insidedata.type == "article" || insidedata.type == "checkout") {
						if (typeof (utag_data) != "undefined" && utag_data && utag_data.purchaseId && utag_data.totalAmount) {
							insidedata.type = "orderconfirmed";
						}
					}
				} catch (tempex) { }

				// Finish identying

				switch (insidedata.type) {
					case "homepage":
						insidedata.name = "Home";
						break;
					case "search":
						if (curpage) {
							searchterm = curpage;
						}

						insidedata.name = "Search Result Page";
						if (searchterm != null && searchterm.length > 0) {
							insidedata.name = decodeURIComponent(searchterm);
							if (insidedata.name.indexOf("+") != -1) {
								insidedata.name = insidedata.name.replace(/\+/g, ' ');
							}
						}

						try {
							if (typeof (utag_data) != "undefined" && utag_data != null && utag_data.internalSearchKeywords) {
								insidedata.name = utag_data.internalSearchKeywords;
							}
						} catch (tempex) { }

						break;
					case "productcategory":
						var tempcat = getCategory();
						if (tempcat != null && tempcat.length > 0) {
							if (tempcat.length > 149)
								tempcat = tempcat.substring(0, 149);
							insidedata.category = tempcat;
						}

						var tempPageName = getPageName();
						if (tempPageName != null && tempPageName.length > 0)
							insidedata.name = tempPageName;

						break;
					case "product":
						var tempPageName = getPageName();
						if (tempPageName != null && tempPageName.length > 0)
							insidedata.name = tempPageName;

						// tempPageName = getProductName();
						// if (tempPageName != null && tempPageName.length > 0)
						// 	insidedata.name = tempPageName;

						// var tempcat = getCategory();
						// if (tempcat != null && tempcat.length > 0) {
						// 	if (tempcat.length > 149)
						// 		tempcat = tempcat.substring(0, 149);
						// 	insidedata.category = tempcat;
						// }

						// var tempval = getProductImage();
						// if (tempval != null && tempval.length > 0) {
						// 	if (tempval.indexOf("?") != -1)
						// 		tempval = tempval.split("?")[0];
						// 	insidedata.img = tempval;
						// }
						// else
						// 	insidedata.type = "other";

						// var tempsku = getProductSku();
						// if (tempsku != null && tempsku.length > 0) {
						// 	insidedata.sku = tempsku;
						// 	insidedata.name = insidedata.name + " - " + tempsku;
						// }
						// else {
						// 	insidedata.type = "other";
						// }

						// var tempprice = getProductPrice();
						// if (tempprice != null && tempprice > 0)
						// 	insidedata.price = tempprice;

						let tempProductViewData = getProductData();
						if (tempProductViewData) {
							if (tempProductViewData.name && tempProductViewData.sku && tempProductViewData.img) {
								insidedata.name = tempProductViewData.name + " - " + tempProductViewData.sku;
								insidedata.sku = tempProductViewData.sku;
								insidedata.img = tempProductViewData.img;
								if (tempProductViewData.price) {
									insidedata.price = tempProductViewData.price;
								}
							}
							else {
								insidedata.type = "other";
							}
						}
						else {
							insidedata.type = "other";
						}

						if (insidedata.type != "other") {
							try {
								if (typeof (utag_data) != "undefined" && utag_data != null) {
									if (utag_data.productCategory) {
										tempcat = utag_data.productCategory;
										if (tempcat != null && tempcat.length > 0) {
											if (tempcat.length > 149)
												tempcat = tempcat.substring(0, 149);
											insidedata.category = tempcat;
										}
									}

									if (utag_data.gender) {
										if (typeof (insidedata.data) == "undefined" || insidedata.data == null) {
											insidedata.data = {};
										}
										insidedata.data.productGender = utag_data.gender;
									}

									if (utag_data.productOnlineSellableStatus) {
										if (typeof (insidedata.data) == "undefined" || insidedata.data == null) {
											insidedata.data = {};
										}
										insidedata.data.productOnlineSellableStatus = utag_data.productOnlineSellableStatus;
									}

									if (utag_data.productStockStatus) {
										if (typeof (insidedata.data) == "undefined" || insidedata.data == null) {
											insidedata.data = {};
										}
										insidedata.data.productStockStatus = utag_data.productStockStatus;
									}
								}
							} catch (tempex) { }
						}

						break;
					case "orderconfirmed":
						insidedata.name = "Order Confirmed";
						break;
					default:
						var tempPageName = getPageName();
						if (tempPageName != null && tempPageName.length > 0)
							insidedata.name = tempPageName;
				}

				if (add_tags.length > 0) {
					insidedata.tags = add_tags.join(",");
				}

				try {
					if (insidedata.type != "homepage" && insidedata.type != "search" && insidedata.type != "checkout" && insidedata.type != "orderconfirmed" && insidedata.type != "login") {
						var tempnode = getNode();
						if (tempnode)
							insidedata.node = tempnode;
					}

				} catch (tempex) { }

				// Get view insidedata from page

				return insidedata;
			}
			catch (ex) {
				log("getViewData error: ", ex);

				var insidedata = {};

				insidedata.action = "trackView";
				insidedata.type = "other";
				insidedata.url = window.location.href;
				insidedata.name = "Error: " + window.location.href;

				return insidedata;
			}
		}

		function getNode() {
			try {
				var tempurl = window.location.href.toLowerCase();
				if (tempurl.indexOf("for-women") != -1 || tempurl.indexOf("/women") != -1) {
					var temprandom = randomIntFromInterval(0, 10);
					if (temprandom < 6) {
						return 4;
					}
					return 6;
				}
				else if (tempurl.indexOf("for-men") != -1 || tempurl.indexOf("/men") != -1) {
					var temprandom = randomIntFromInterval(0, 10);
					if (temprandom < 6) {
						return 7;
					}
					return 10;
				}

				if (utag_data.productCategory && utag_data.gender) {
					if (utag_data.gender == "women") {
						if (utag_data.productCategory.indexOf("access") != -1 || utag_data.productCategory.indexOf("perfume") != -1)
							return 6;
						return 4;
					}
					else if (utag_data.gender == "men") {
						if (utag_data.productCategory.indexOf("access") != -1 || utag_data.productCategory.indexOf("wallet") != -1 || utag_data.productCategory.indexOf("bag") != -1)
							return 10;
						return 7;
					}
				}
			} catch (tempex) { }
			return 5;
		}

		function getPageName() {
			// Modify if necessary
			try {
				var content = document.getElementsByTagName("title");
				if (typeof (content) != "undefined" && content != null && content.length > 0) {
					var result = content[0].textContent || content[0].innerText;
					if (typeof (result) != "undefined" && result != null && result.length > 0) {
						return myTrim(result);
					}
				}
			} catch (pagenameex) { }

			return null;
		}

		function getProductName() {
			try {
				let ldjsons = _insideJQ('script[type="application/ld+json"]');
				for (let i = 0; i < ldjsons.length; i++) {
					let tempdata = JSON.parse(_insideJQ(ldjsons[i]).last().html().replace(/\n/g, ""));
					if (typeof (tempdata) != "undefined" && tempdata != null && _insideJQ.isArray(tempdata)) {
						for (let l = 0; l < tempdata.length; l++) {
							let tempdetail = tempdata[i];
							if (typeof (tempdetail) != "undefined" && tempdetail != null && typeof (tempdetail["@type"]) != "undefined" && tempdetail["@type"] != null && tempdetail["@type"] == "Product" && typeof (tempdetail.sku) != "undefined" && tempdetail.sku != null && tempdetail.sku.length > 0) {
								if (_insideJQ.isArray(tempdetail.name)) {
									return tempdetail.name[0];
								}
								else
									return tempdetail.name;
							}
						}
					}
					else if (typeof (tempdata) != "undefined" && tempdata != null && typeof (tempdata["@type"]) != "undefined" && tempdata["@type"] != null && tempdata["@type"] == "Product" && typeof (tempdata.sku) != "undefined" && tempdata.sku != null && tempdata.sku.length > 0) {
						if (_insideJQ.isArray(tempdata.name)) {
							return tempdata.name[0];
						}
						else
							return tempdata.name;
					}
				}
			}
			catch (tempex) {
			}

			try {
				if (typeof (utag_data) != "undefined" && utag_data != null && utag_data.productName) {
					return utag_data.productName;
				}
			} catch (tempex) { }

			return null;
		}

		function getProductImage() {
			try {
				let ldjsons = _insideJQ('script[type="application/ld+json"]');
				for (let i = 0; i < ldjsons.length; i++) {
					let tempdata = JSON.parse(_insideJQ(ldjsons[i]).last().html().replace(/\n/g, ""));
					if (typeof (tempdata) != "undefined" && tempdata != null && _insideJQ.isArray(tempdata)) {
						for (let l = 0; l < tempdata.length; l++) {
							let tempdetail = tempdata[i];
							if (typeof (tempdetail) != "undefined" && tempdetail != null && typeof (tempdetail["@type"]) != "undefined" && tempdetail["@type"] != null && tempdetail["@type"] == "Product" && typeof (tempdetail.image) != "undefined" && tempdetail.image != null && tempdetail.image.length > 0) {
								if (_insideJQ.isArray(tempdetail.image)) {
									if (tempdetail.image[0] && tempdetail.image[0].url)
										return tempdetail.image[0].url;
								}
								else {
									if (tempdetail.image && tempdetail.image.url)
										return tempdetail.image.url;
								}
							}
						}
					}
					else if (typeof (tempdata) != "undefined" && tempdata != null && typeof (tempdata["@type"]) != "undefined" && tempdata["@type"] != null && tempdata["@type"] == "Product" && typeof (tempdata.image) != "undefined" && tempdata.image != null && tempdata.image.length > 0) {
						if (_insideJQ.isArray(tempdata.image)) {
							if (tempdata.image[0] && tempdata.image[0].url)
								return tempdata.image[0].url;
						}
						else
							if (tempdata.image && tempdata.image.url)
								return tempdata.image.url;
					}
				}
			}
			catch (tempex) {
			}

			try {
				const tempImageEle = _insideJQ(".lv-product .lv-product-page-header__primary .lv-product-picture img.lv-smart-picture__object");
				if (tempImageEle.length > 0)
					return tempImageEle.get(0).currentSrc;
			} catch (tempex) { }

			// try {
			// 	var metaTags = document.getElementsByTagName("meta");

			// 	var fbAppIdContent = "";
			// 	for (var i = 0; i < metaTags.length; i++) {
			// 		if (metaTags[i].getAttribute("property") == "og:image") {
			// 			fbAppIdContent = metaTags[i].getAttribute("content");
			// 			if (fbAppIdContent)
			// 				return fbAppIdContent;
			// 		}
			// 	}
			// }
			// catch (tempex) {
			// }

			return null;
		}

		function getProductPrice() {
			try {
				if (typeof (utag_data) != "undefined" && utag_data != null && utag_data.price) {
					return utag_data.price;
				}
			} catch (tempex) { }

			try {
				let ldjsons = _insideJQ('script[type="application/ld+json"]');
				for (let i = 0; i < ldjsons.length; i++) {
					let tempdata = JSON.parse(_insideJQ(ldjsons[i]).last().html().replace(/\n/g, ""));
					if (typeof (tempdata) != "undefined" && tempdata != null && _insideJQ.isArray(tempdata)) {
						for (let l = 0; l < tempdata.length; l++) {
							let tempdetail = tempdata[i];
							if (typeof (tempdetail) != "undefined" && tempdetail != null && typeof (tempdetail["@type"]) != "undefined" && tempdetail["@type"] != null && tempdetail["@type"] == "Product" && tempdetail.offers && typeof (tempdetail.offers.price) != "undefined" && tempdetail.offers.price != null && tempdetail.offers.price) {
								if (_insideJQ.isArray(tempdetail.offers.price)) {
									return tempdetail.offers.price[0];
								}
								else
									return tempdetail.offers.price;
							}
						}
					}
					else if (typeof (tempdata) != "undefined" && tempdata != null && typeof (tempdata["@type"]) != "undefined" && tempdata["@type"] != null && tempdata["@type"] == "Product" && tempdata.offers && typeof (tempdata.offers.price) != "undefined" && tempdata.offers.price != null && tempdata.offers.price) {
						if (_insideJQ.isArray(tempdata.offers.price)) {
							return tempdata.offers.price[0];
						}
						else
							return tempdata.offers.price;
					}
				}
			}
			catch (tempex) {
			}

			return null;
		}

		/*function getProductSku() {
			var _urlSku = null;
			try { _urlSku = window.location.pathname.split("/").filter(Boolean).pop(); } catch(e) {}
	
			try {
				if (typeof (utag_data) != "undefined" && utag_data != null && utag_data.productSku) {
					console.log("[INSIDE SKU] returning utag_data.productSku:", utag_data.productSku, "| URL SKU:", _urlSku, "| match:", utag_data.productSku === _urlSku);
					return utag_data.productSku;
				}
			} catch (tempex) { }

			try {
				let ldjsons = _insideJQ('script[type="application/ld+json"]');
				for (let i = 0; i < ldjsons.length; i++) {
					let tempdata = JSON.parse(_insideJQ(ldjsons[i]).last().html().replace(/\n/g, ""));
					if (typeof (tempdata) != "undefined" && tempdata != null && _insideJQ.isArray(tempdata)) {
						for (let l = 0; l < tempdata.length; l++) {
							let tempdetail = tempdata[l];
							if (typeof (tempdetail) != "undefined" && tempdetail != null && typeof (tempdetail["@type"]) != "undefined" && tempdetail["@type"] != null && tempdetail["@type"] == "Product" && typeof (tempdetail.sku) != "undefined" && tempdetail.sku != null && tempdetail.sku.length > 0) {
								if (_insideJQ.isArray(tempdetail.sku)) {
									console.log("[INSIDE SKU] returning ld+json sku:", tempdetail.sku[0], "| URL SKU:", _urlSku);
									return tempdetail.sku[0];
								}
								else {
									console.log("[INSIDE SKU] returning ld+json sku:", tempdetail.sku, "| URL SKU:", _urlSku);
									return tempdetail.sku;
								}
							}
						}
					}
					else if (typeof (tempdata) != "undefined" && tempdata != null && typeof (tempdata["@type"]) != "undefined" && tempdata["@type"] != null && tempdata["@type"] == "Product" && typeof (tempdata.sku) != "undefined" && tempdata.sku != null && tempdata.sku.length > 0) {
						if (_insideJQ.isArray(tempdata.sku)) {
							console.log("[INSIDE SKU] returning ld+json sku:", tempdetail.sku[0], "| URL SKU:", _urlSku);
							return tempdata.sku[0];
						}
						else {
							console.log("[INSIDE SKU] returning ld+json sku:", tempdetail.sku, "| URL SKU:", _urlSku);
							return tempdata.sku;
						}
					}
				}
			}
			catch (tempex) {
			}

			try {
				const lastPart = window.location.pathname.split("/").filter(Boolean).pop();
				if (lastPart) {
					console.log("[INSIDE SKU] returning URL SKU:", lastPart);
					return lastPart;
				}
			} catch (tempex) { }

			console.log("[INSIDE SKU] no SKU found");
			return null;
		}*/

		function getProductSku() {
			var skuFromUtag = null;
			var skuFromUrl = null;

			try {
				if (typeof (utag_data) != "undefined" && utag_data != null && utag_data.productSku) {
					skuFromUtag = utag_data.productSku;
				}
			} catch (tempex) { }

			try {
				if (window.location.pathname.indexOf("/products/") !== -1) {
					var lastPart = window.location.pathname.split("/").filter(Boolean).pop();
					if (lastPart) {
						skuFromUrl = lastPart;
					}
				}
			} catch (tempex) { }

			if (skuFromUrl) {
				if (skuFromUtag && skuFromUtag !== skuFromUrl) {
					// console.warn("[INSIDE SKU] mismatch - utag:", skuFromUtag, "url:", skuFromUrl, "- using URL");
				} else {
					// console.log("[INSIDE SKU] returning:", skuFromUrl, "| utag:", skuFromUtag, "| source:", skuFromUtag === skuFromUrl ? "both" : "url");
				}
				return skuFromUrl;
			}

			if (skuFromUtag) {
				try {
					let ldjsons = _insideJQ('script[type="application/ld+json"]');
					for (let i = 0; i < ldjsons.length; i++) {
						let tempdata = JSON.parse(_insideJQ(ldjsons[i]).last().html().replace(/\n/g, ""));
						if (typeof (tempdata) != "undefined" && tempdata != null && _insideJQ.isArray(tempdata)) {
							for (let l = 0; l < tempdata.length; l++) {
								let tempdetail = tempdata[l];
								if (typeof (tempdetail) != "undefined" && tempdetail != null && typeof (tempdetail["@type"]) != "undefined" && tempdetail["@type"] != null && tempdetail["@type"] == "Product" && typeof (tempdetail.sku) != "undefined" && tempdetail.sku != null && tempdetail.sku.length > 0) {
									var ldSku = _insideJQ.isArray(tempdetail.sku) ? tempdetail.sku[0] : tempdetail.sku;
									if (ldSku === skuFromUtag) {
										// console.log("[INSIDE SKU] returning:", skuFromUtag, "| source: utag+ldjson confirmed");
										return skuFromUtag;
									}
									// console.warn("[INSIDE SKU] utag/ldjson mismatch - utag:", skuFromUtag, "ldjson:", ldSku, "- returning null");
									return null;
								}
							}
						}
						else if (typeof (tempdata) != "undefined" && tempdata != null && typeof (tempdata["@type"]) != "undefined" && tempdata["@type"] != null && tempdata["@type"] == "Product" && typeof (tempdata.sku) != "undefined" && tempdata.sku != null && tempdata.sku.length > 0) {
							var ldSku = _insideJQ.isArray(tempdata.sku) ? tempdata.sku[0] : tempdata.sku;
							if (ldSku === skuFromUtag) {
								// console.log("[INSIDE SKU] returning:", skuFromUtag, "| source: utag+ldjson confirmed");
								return skuFromUtag;
							}
							// console.warn("[INSIDE SKU] utag/ldjson mismatch - utag:", skuFromUtag, "ldjson:", ldSku, "- returning null");
							return null;
						}
					}
				}
				catch (tempex) {
				}

				// console.log("[INSIDE SKU] returning:", skuFromUtag, "| source: utag only (no ldjson found)");
				return skuFromUtag;
			}

			// console.log("[INSIDE SKU] no SKU found");
			return null;
		}

		function getProductData() {
			let skuFromUtag = null;
			let skuFromUrl = null;
			let insideProductData = {};

			try {
				if (window.location.pathname.indexOf("/products/") !== -1) {
					let lastPart = window.location.pathname.split("/").filter(Boolean).pop();
					if (lastPart) {
						skuFromUrl = lastPart;
					}
				}
			} catch (tempex) { }

			try {
				if (typeof (utag_data) != "undefined" && utag_data != null && utag_data.productSku && utag_data.productSku == skuFromUrl) {
					skuFromUtag = utag_data.productSku;
				}
			} catch (tempex) { }

			if (skuFromUrl && skuFromUtag) {
				if (skuFromUtag && skuFromUtag !== skuFromUrl) {
					// console.warn("[INSIDE SKU] mismatch - utag:", skuFromUtag, "url:", skuFromUrl, "- using URL");
				} else {
					// console.log("[INSIDE SKU] returning:", skuFromUrl, "| utag:", skuFromUtag, "| source:", skuFromUtag === skuFromUrl ? "both" : "url");
					insideProductData.sku = skuFromUrl;
					if (utag_data.price) {
						insideProductData.price = utag_data.price;
					}
					if (utag_data.productName) {
						insideProductData.name = utag_data.productName;
					}
					if (utag_data.productCategory) {
						insideProductData.category = utag_data.productCategory;
					}

					try {
						let tempImageEle = _insideJQ(".lv-product .lv-product-page-header__primary .lv-product-picture img.lv-smart-picture__object");
						if (tempImageEle.length > 0)
							insideProductData.img = tempImageEle.get(0).currentSrc;
					} catch (tempex) { }
				}
			}

			if (skuFromUtag) {
				try {
					let ldjsons = _insideJQ('script[type="application/ld+json"]');
					for (let i = 0; i < ldjsons.length; i++) {
						let tempdata = JSON.parse(_insideJQ(ldjsons[i]).last().html().replace(/\n/g, ""));
						if (typeof (tempdata) != "undefined" && tempdata != null && _insideJQ.isArray(tempdata)) {
							for (let l = 0; l < tempdata.length; l++) {
								let tempdetail = tempdata[l];
								if (typeof (tempdetail) != "undefined" && tempdetail != null && typeof (tempdetail["@type"]) != "undefined" && tempdetail["@type"] != null && tempdetail["@type"] == "Product" && typeof (tempdetail.sku) != "undefined" && tempdetail.sku != null && tempdetail.sku.length > 0) {
									let ldSku = _insideJQ.isArray(tempdetail.sku) ? tempdetail.sku[0] : tempdetail.sku;
									if (ldSku === skuFromUtag) {
										// console.log("[INSIDE SKU] returning:", skuFromUtag, "| source: utag+ldjson confirmed");
										insideProductData.sku = skuFromUrl;
										// if (tempdetail.offers && typeof (tempdetail.offers.price) != "undefined" && tempdetail.offers.price != null && tempdetail.offers.price) {
										// 	insideProductData.price = _insideJQ.isArray(tempdetail.offers.price) ? tempdetail.offers.price[0] : tempdetail.offers.price;
										// }
										// if (tempdetail.name) {
										// 	insideProductData.name = _insideJQ.isArray(tempdetail.name) ? tempdetail.name[0] : tempdetail.name;
										// }
										if (_insideJQ.isArray(tempdetail.image)) {
											if (tempdetail.image[0] && tempdetail.image[0].url && tempdetail.image[0].url.toLowerCase().indexOf(skuFromUrl.toLowerCase()) != -1) {
												insideProductData.img = tempdetail.image[0].url;
											}
										}
										else {
											if (tempdetail.image && tempdetail.image.url && tempdetail.image.url.toLowerCase().indexOf(skuFromUrl.toLowerCase()) != -1)
												insideProductData.img = tempdetail.image.url;
										}
									}

									break;
								}
							}
						}
						else if (typeof (tempdata) != "undefined" && tempdata != null && typeof (tempdata["@type"]) != "undefined" && tempdata["@type"] != null && tempdata["@type"] == "Product" && typeof (tempdata.sku) != "undefined" && tempdata.sku != null && tempdata.sku.length > 0) {
							var ldSku = _insideJQ.isArray(tempdata.sku) ? tempdata.sku[0] : tempdata.sku;
							if (ldSku === skuFromUtag) {
								// console.log("[INSIDE SKU] returning:", skuFromUtag, "| source: utag+ldjson confirmed");
								insideProductData.sku = skuFromUrl;
								// if (tempdata.offers && typeof (tempdata.offers.price) != "undefined" && tempdata.offers.price != null && tempdata.offers.price) {
								// 	insideProductData.price = _insideJQ.isArray(tempdata.offers.price) ? tempdata.offers.price[0] : tempdata.offers.price;
								// }
								// if (tempdata.name) {
								// 	insideProductData.name = _insideJQ.isArray(tempdata.name) ? tempdata.name[0] : tempdata.name;
								// }
								if (_insideJQ.isArray(tempdata.image)) {
									if (tempdata.image[0] && tempdata.image[0].url && tempdata.image[0].url.toLowerCase().indexOf(skuFromUrl.toLowerCase()) != -1)
										insideProductData.img = tempdata.image[0].url;
								}
								else {
									if (tempdata.image && tempdata.image.url && tempdata.image.url.toLowerCase().indexOf(skuFromUrl.toLowerCase()) != -1)
										insideProductData.img = tempdata.image.url;
								}
							}
						}
					}
				}
				catch (tempex) {
				}

				return insideProductData;
			}

			// console.log("[INSIDE SKU] no SKU found");
			return null;
		}

		function getCategory() {
			try {
				var breadcrumbs = _insideJQ(".breadcrumbs");

				if (breadcrumbs != null && breadcrumbs.length > 0) {
					var path = "";
					for (var i = 1; i < breadcrumbs.length; i++) {
						var temp = breadcrumbs[i].innerText || breadcrumbs[i].textContent;
						var tempelem = breadcrumbs[i].getElementsByTagName("a");
						if (tempelem != null && tempelem.length > 0) {
							temp = tempelem[0].innerText || tempelem[0].textContent;
						}
						temp = myTrim(temp);
						if (temp != "/")
							path += (path != "" ? " / " : "") + temp;
					}
					if (path != "")
						return path;

				}
			}
			catch (tempex) {
			}

			try {
				if (typeof (utag_data) != "undefined" && utag_data != null && utag_data.productCategory) {
					return utag_data.productCategory;
				}
			} catch (tempex) { }

			return null;
		}

		function getOrderData() {
			try {
				var data = [];
				var totalprice = 0;
				var orderId = "auto";

				_insideJQ(".lv-header-mini-cart:first .lv-header-mini-cart__products .lv-header-mini-cart__product-item").each(function (index) {
					var tempitem = _insideJQ(this);
					var insideitem = {};
					insideitem.action = "addItem";
					insideitem.orderId = orderId;
					var tempimg = tempitem.find(".lv-smart-picture img").get(0).currentSrc;
					if (tempimg) {
						insideitem.img = tempimg;
					}
					insideitem.qty = 1;

					insideitem.name = myTrim(tempitem.find(".lv-product-card__name").text());
					insideitem.sku = insideitem.name;

					var tempprice = tempitem.find(".lv-product-card__price").text();
					var decimalSign = getDecimalSign(myTrim(tempprice.replace(/[^\d.,]/g, '')));
					if (decimalSign == ",") {
						tempprice = tempprice.replace(/[.]/g, "");
						tempprice = tempprice.replace(",", ".");
					}
					insideitem.price = parseFloat(tempprice.replace(/[^0-9\.\-\+]/g, ""));

					try {
						var tempsku = tempitem.find(".lv-product-card__name").attr("id");;
						if (tempsku) {
							insideitem.sku = tempsku;
							if (insideitem.sku.indexOf("product-") != -1) {
								insideitem.sku = insideitem.sku.split("product-")[1];
							}
						}
					} catch (tempex) { }

					totalprice = totalprice + insideitem.price;
					insideitem.price = insideitem.price / insideitem.qty;

					data.push(insideitem);
				});

				if (data.length > 0) {

					data.push({
						"action": "trackOrder",
						"orderId": orderId,
						"orderTotal": totalprice
					});

					sessionStorage.setItem("insideordertotal", totalprice);

					return data;
				}
			}
			catch (ex) {
				log("getOrderData error. ", ex);
			}

			try {
				var data = [];
				var totalprice = 0;
				var orderId = "auto";

				if (typeof (utag_data) != "undefined" && utag_data != null && utag_data.quantity) {
					var tempqtysplit = utag_data.quantity.split(",");
					var tempimgs = _insideJQ("img.lv-smart-picture__object");
					if (tempimgs.length == 0) {
						tempimgs = _insideJQ(".lv-product-picture img");
					}

					_insideJQ.each(tempqtysplit, function (tempindex, tempqty) {
						var insideitem = {};
						insideitem.action = "addItem";
						insideitem.orderId = orderId;
						insideitem.name = utag_data.productName.split(",")[tempindex];
						insideitem.price = parseFloat(utag_data.price.split(",")[tempindex]);
						insideitem.qty = parseFloat(tempqty);
						insideitem.sku = utag_data.productSku.split(",")[tempindex];;
						try {
							if (tempimgs.length > 0) {
								tempimgs.each(function (rowindex) {
									var tempalt = _insideJQ(this).get(0).currentSrc;
									if (tempalt.toLowerCase().indexOf(insideitem.sku.toLowerCase()) != -1) {
										insideitem.img = tempalt;
									}
								});
							}
						} catch (imgex) { log(imgex) }

						if (insideitem.name && insideitem.sku && insideitem.qty) {
							totalprice = totalprice + (insideitem.qty * insideitem.price);

							data.push(insideitem);
						}
					});
				}

				if (data.length > 0) {
					try {
						if (typeof (utag_data) != "undefined" && utag_data != null && utag_data.totalAmount && isNumeric(utag_data.totalAmount)) {
							totalprice = parseFloat(utag_data.totalAmount);
						}
					} catch (totalex) { }

					data.push({
						"action": "trackOrder",
						"orderId": orderId,
						"orderTotal": totalprice
					});

					sessionStorage.setItem("insideordertotal", totalprice);

					return data;
				}
			}
			catch (ex) {
				log("getOrderData error. ", ex);
			}

			return null;
		}

		function orderConfirmProcess() {
			try {
				var data = [];
				var tempcurrency = null;

				var detail = null;
				if (typeof (utag_data) != "undefined" && utag_data != null && utag_data.purchaseId && utag_data.totalAmount) {
					detail = utag_data;
				}

				if (detail != null) {
					var totalprice = detail.totalAmount;
					var orderID = detail.purchaseId;
					var temppurchasedata = {};

					try {
						if (typeof (detail.shippingCost) != "undefined" && detail.shippingCost != null) {
							temppurchasedata.shipping = detail.shippingCost;
						}
						if (tempcurrency != null) {
							temppurchasedata.currency = tempcurrency;
						}

						if (typeof (dataLayer) != "undefined" && dataLayer != null && dataLayer.length > 0) {
							for (let i = dataLayer.length - 1; i >= 0; i--) {
								if (typeof (dataLayer[i]) != "undefined" && dataLayer[i] != null && dataLayer[i][1] == "purchase" && dataLayer[i][2] && dataLayer[i][2].transaction_id && dataLayer[i][2].currency_code && dataLayer[i][2].items && dataLayer[i][2].items.length > 0) {
									_insideJQ.each(dataLayer[i][2].items, function (index, tempItemDetail) {
										let tempInsideItem = {};
										tempInsideItem.action = "addItem";
										tempInsideItem.orderId = "auto";
										tempInsideItem.name = tempItemDetail.item_name;
										tempInsideItem.price = parseFloat(tempItemDetail.price);
										tempInsideItem.qty = parseFloat(tempItemDetail.quantity);
										tempInsideItem.sku = tempItemDetail.item_id;

										try {
											if (tempItemDetail.item_category) {
												tempInsideItem.category = tempItemDetail.item_category;
												if (tempInsideItem.category.length > 149)
													tempInsideItem.category = tempInsideItem.category.substring(0, 149);
											}
										} catch (tempex) { }

										data.push(tempInsideItem);
									});

									break;
								}
							}
						}
					} catch (tempex) { }

					try {
						if (data.length == 0) {
							if (typeof (utag_data) != "undefined" && utag_data != null && utag_data.quantity) {
								let tempqtysplit = utag_data.quantity.split(",");

								_insideJQ.each(tempqtysplit, function (tempindex, tempqty) {
									let insideitem = {};
									insideitem.action = "addItem";
									insideitem.orderId = "auto";
									insideitem.name = utag_data.productName.split(",")[tempindex];
									insideitem.price = parseFloat(utag_data.price.split(",")[tempindex]);
									insideitem.qty = parseFloat(tempqty);
									insideitem.sku = utag_data.productSku.split(",")[tempindex];

									if (insideitem.name && insideitem.sku && insideitem.qty) {
										data.push(insideitem);
									}
								});
							}
						}
					} catch (tempex) { }

					if (typeof (orderID) != "undefined" && orderID != null && orderID.length > 0 && orderID != "auto") {
						let updateBool = true;
						try {
							var lastOrderID = sessionStorage.getItem("insidelastorderid");
							if (lastOrderID == orderID) {
								return null;
							}

							if (data.length > 0) {
								updateBool = false;
							}
						}
						catch (orderidex) {
						}

						data.push({
							"action": "trackOrder",
							"orderId": "auto",
							"newOrderId": orderID,
							"orderTotal": totalprice,
							"data": temppurchasedata,
							"update": updateBool,
							"complete": true
						});

						return data;
					}
				}
			}
			catch (ex) {
				log("orderConfirmProcess error. ", ex);
			}

			try {
				let data = [];
				let tempcurrency = null;

				let detail = null;
				if (typeof (dataLayer) != "undefined" && dataLayer != null && dataLayer.length > 0) {
					for (let i = dataLayer.length - 1; i >= 0; i--) {
						if (typeof (dataLayer[i]) != "undefined" && dataLayer[i] != null && typeof (dataLayer[i].ecommerce) != "undefined" && dataLayer[i].ecommerce != null && typeof (dataLayer[i].ecommerce.transaction_id) != "undefined" && dataLayer[i].ecommerce.transaction_id != null && dataLayer[i].ecommerce.transaction_id && typeof (dataLayer[i].ecommerce.value) != "undefined" && dataLayer[i].ecommerce.value != null) {
							detail = dataLayer[i].ecommerce;
						}
					}
				}

				if (detail != null) {
					let totalprice = detail.value;
					let orderID = detail.transaction_id;
					let temppurchasedata = {};

					try {
						if (typeof (detail.shipping) != "undefined" && detail.shipping != null) {
							temppurchasedata.shipping = detail.shipping;
						}
						if (typeof (detail.tax) != "undefined" && detail.tax != null) {
							temppurchasedata.tax = detail.tax;
						}
						if (tempcurrency != null) {
							temppurchasedata.currency = tempcurrency;
						}

						let itemDetails = detail.items;

						for (let i = 0; i < itemDetails.length; i++) {
							let tempInsideItem = {};
							tempInsideItem.action = "addItem";
							tempInsideItem.orderId = "auto";
							tempInsideItem.name = itemDetails[i].item_name;
							tempInsideItem.price = parseFloat(itemDetails[i].price);
							tempInsideItem.qty = parseFloat(itemDetails[i].quantity);
							tempInsideItem.sku = itemDetails[i].item_id;

							try {
								if (itemDetails[i].item_category) {
									tempInsideItem.category = itemDetails[i].item_category;
									if (tempInsideItem.category.length > 149)
										tempInsideItem.category = tempInsideItem.category.substring(0, 149);
								}
							} catch (tempex) { }

							data.push(tempInsideItem);
						}
					} catch (tempex) { }

					try {
						if (data.length == 0) {
							if (typeof (utag_data) != "undefined" && utag_data != null && utag_data.quantity) {
								let tempqtysplit = utag_data.quantity.split(",");

								_insideJQ.each(tempqtysplit, function (tempindex, tempqty) {
									let insideitem = {};
									insideitem.action = "addItem";
									insideitem.orderId = "auto";
									insideitem.name = utag_data.productName.split(",")[tempindex];
									insideitem.price = parseFloat(utag_data.price.split(",")[tempindex]);
									insideitem.qty = parseFloat(tempqty);
									insideitem.sku = utag_data.productSku.split(",")[tempindex];

									if (insideitem.name && insideitem.sku && insideitem.qty) {
										data.push(insideitem);
									}
								});
							}
						}
					} catch (tempex) { }

					if (typeof (orderID) != "undefined" && orderID != null && orderID != "auto") {

						let updateBool = true;
						try {
							var lastOrderID = sessionStorage.getItem("insidelastorderid");
							if (lastOrderID == orderID) {
								return null;
							}

							if (data.length > 0) {
								updateBool = false;
							}
						}
						catch (orderidex) {
						}

						data.push({
							"action": "trackOrder",
							"orderId": "auto",
							"newOrderId": orderID,
							"orderTotal": totalprice,
							"data": temppurchasedata,
							"update": updateBool,
							"complete": true
						});
					}

					return data;
				}
			}
			catch (ex) {
				log("orderConfirmProcess error. ", ex);
			}

			return null;
		}

		function getVisitorId() {
			try {
				if (typeof (_insideData.user.id) != "undefined" && _insideData.user.id != null && typeof (_insideData.user.email) != "undefined" && _insideData.user.email != null && validateEmail(_insideData.user.email))
					return _insideData.user.id;
			}
			catch (visitidex) {
			}

			return null;
		}

		function getVisitorName() {
			try {
				if (typeof (_insideData.user.id) != "undefined" && _insideData.user.id != null && typeof (_insideData.user.email) != "undefined" && _insideData.user.email != null && validateEmail(_insideData.user.email)) {
					if (_insideData.user.name) {
						return _insideData.user.name;
					}
				}
			}
			catch (visitidex) {
			}

			return null;
		}

		function getVisitorData() {
			try {
				if (typeof (utag_data) != "undefined" && utag_data != null) {
					var tempdata = {};

					if (utag_data.environmentLanguage) {
						tempdata.language = utag_data.environmentLanguage;
						if (tempdata.language.indexOf("-") != -1) {
							tempdata.language = tempdata.language.split("-")[0];
						}
					}
					if (utag_data.environmentVersion) {
						tempdata.country = utag_data.environmentVersion;
					}

					let tempuserid = getVisitorId();
					let tempusername = getVisitorName();
					if (tempuserid != null && tempuserid.length > 0 && tempusername != null && tempusername.length > 0) {
						tempdata.user_name = tempusername;
						tempdata.user_email = _insideData.user.email;
					}

					return tempdata;
				}
			}
			catch (visitidex) {
			}

			return null;
		}

		function insertInsideTag() {
			try {
				_insideGraph.processQueue();
			}
			catch (tempex) {
			}
		}

		function sendToInside() {
			try {
				tracker.url = window.location.href;

				var visitorId = getVisitorId();
				if (visitorId != null && visitorId.length > 0) {
					tracker.visitorId = visitorId;
				}

				var visitorName = getVisitorName();
				if (visitorName != null && visitorName.length > 0) {
					tracker.visitorName = visitorName;
				}

				var visitorData = getVisitorData();
				if (visitorData != null) {
					tracker.visitorData = visitorData;
				}

				var view = getViewData();
				if (view != null) {
					if (view.type == "orderconfirmed") {
						var tempconfirm = orderConfirmProcess();
						if (tempconfirm != null && tempconfirm.length > 0) {
							for (var i = 0; i < tempconfirm.length; i++) {
								_inside.push(tempconfirm[i]);

								try {
									if (tempconfirm[i].action == "trackOrder")
										if (typeof (tempconfirm[i].newOrderId) != "undefined" && tempconfirm[i].newOrderId != null)
											sessionStorage.setItem("insidelastorderid", tempconfirm[i].newOrderId);
								}
								catch (tempex) {
								}
							}

							sessionStorage.removeItem("insideordertotal");
						}
						else {
							view.type == "other";
						}
					}
					else {
						var orderData = getOrderData();

						if (orderData != null && orderData.length > 0) {
							for (var i = 0; i < orderData.length; i++) {
								_inside.push(orderData[i]);
								if (orderData[i].action == "trackOrder") {
									view.orderId = orderData[i].orderId;
									view.orderTotal = orderData[i].orderTotal;
									insideOrderTotal = orderData[i].orderTotal;
								}
							}
						}
						else {
							try {
								if (view.url.indexOf("/cart") != -1) {
									sessionStorage.removeItem("insideordertotal");
								}
								else {
									var temptotal = sessionStorage.getItem("insideordertotal");
									if (temptotal != null) {
										var tempcount = _insideJQ(".lv-header__utility-item.-cart .lv-icon-with-count").text();
										if (tempcount) {
											tempcount = parseFloat(tempcount.replace(/[^0-9\.\-\+]/g, ""));

											if (isNumeric(tempcount) && tempcount > 0) {
												view.orderId = "auto";
												view.orderTotal = temptotal;
											}
										}
									}
								}
							} catch (tempex) { }
						}
					}

					// Add currency code
					try {
						try {
							if (typeof (utag_data) != "undefined" && utag_data != null && utag_data.currency_code) {
								_insideCurrency = utag_data.currency_code;
							}
							if (typeof (utag_data) != "undefined" && utag_data != null && utag_data.currencyCode) {
								_insideCurrency = utag_data.currencyCode;
							}
						} catch (currencyex) { }

						if (_insideCurrency) {
							if (_inside != null && _inside.length > 0) {
								for (var i = 0; i < _inside.length; i++) {
									if (_inside[i].action == "trackOrder") {
										if (typeof (_inside[i].data) == "undefined" || _inside[i].data == null) {
											_inside[i].data = {};
										}

										if (typeof (_inside[i].data.currency) == "undefined" || _inside[i].data.currency == null) {
											_inside[i].data.currency = _insideCurrency;
										}
									}
								}
							}

							if (typeof (view.data) == "undefined" || view.data == null) {
								view.data = {};
							}
							view.data.currency = _insideCurrency;

							if (typeof (tracker.visitorData) == "undefined" || tracker.visitorData == null) {
								tracker.visitorData = {};
							}
							tracker.visitorData.currency = _insideCurrency;
						}
					} catch (currencyex) { }

					try {
						_insideCurUrl = window.location.href;
						_insideCurPageType = view.type;

						if (view.type == "product") {
							if (typeof (dataLayer) != "undefined" && dataLayer != null && dataLayer.length > 0) {
								_insideDataLayerIndex = dataLayer.length - 1;
								_insideProdUrl = window.location.href;
								_insideEventLabelTest = "";
								_insideAddToCart = null;
								deferWait(function () {
									_insideDataLayerIndex = dataLayer.length - 1;
									if (_insideEventLabelTest)
										callEventListener(_insideEventLabelTest);
								}, function () {
									if (typeof (_insideGraph) != "undefined" && _insideGraph != null && typeof (insideFrontInterface) != "undefined" && insideFrontInterface != null && insideFrontInterface.triggerVisitorEvent) {
										for (var i = _insideDataLayerIndex; i < dataLayer.length; i++) {
											if (typeof (dataLayer[i]) != "undefined" && dataLayer[i] && dataLayer[i][0] && dataLayer[i][0] == "event" && dataLayer[i][1] && dataLayer[i][1] == "interaction") {
												if (dataLayer[i][2].event_label) {
													var tempEventLabel = dataLayer[i][2].event_label;
													if (tempEventLabel == "open_product_details") {
														_insideEventLabelTest = tempEventLabel;
														return true;
													}
												}
											}
										}
									}

									if (_insideProdUrl != window.location.href) {
										return true;
									}

									return false;
								});

								// deferWait(function () {
								// 	try {
								// 		_insideDataLayerIndex = dataLayer.length - 1;
								// 		if (_insideAddToCart) {
								// 			_insideGraph.current.addItem({
								// 				"orderId": "auto",
								// 				"sku": _insideAddToCart.item_id,
								// 				"name": _insideAddToCart.item_name,
								// 				"price": parseFloat(_insideAddToCart.price),
								// 				"qty": parseFloat(_insideAddToCart.quantity)
								// 			});

								// 			_insideGraph.current.trackOrder({
								// 				"orderId": "auto",
								// 				"update": true
								// 			});
								// 		}
								// 	} catch (tempex) { }
								// }, function () {
								// 	if (typeof (_insideGraph) != "undefined" && _insideGraph != null && typeof (insideFrontInterface) != "undefined" && insideFrontInterface != null && insideFrontInterface.triggerVisitorEvent) {
								// 		for (var i = _insideDataLayerIndex; i < dataLayer.length; i++) {
								// 			if (typeof (dataLayer[i]) != "undefined" && dataLayer[i] && dataLayer[i][0] && dataLayer[i][0] == "event" && dataLayer[i][1] && dataLayer[i][1] == "add_to_cart") {
								// 				if (dataLayer[i][2].event_action && dataLayer[i][2].event_action == "add_to_cart_succeeded" && dataLayer[i][2].items && dataLayer[i][2].items.length > 0) {
								// 					_insideAddToCart = dataLayer[i][2].items[0];
								// 					return true;
								// 				}
								// 			}
								// 		}
								// 	}

								// 	if (_insideProdUrl != window.location.href) {
								// 		return true;
								// 	}

								// 	return false;
								// });
							}
						}
					} catch (tempex) { }

					_inside.push(view);

					log("Inside Debug: ", _inside);
				}
			}
			catch (sendex) {
				_inside = [];

				_inside.push({
					"action": "trackView",
					"type": "other",
					"name": "Check: " + window.location.href
				});

				log(sendex);
			}

			insertInsideTag();
			if (!_insideFirstLoad)
				_insideFirstLoad = true;
		}

		window._insideViewUpdate = debounce(function () {
			var triggerupdate = true;
			try {
				var tempcurview = getViewData();
				if (_insideCurUrl != window.location.href) {
					_insideCurUrl = window.location.href;
					_insideCurPageType = tempcurview.type;
				}

				// var temphashj = hashJoaat(JSON.stringify(_insideDataLayer))
				// if (temphashj == _insideHashJ)
				// 	triggerupdate = false;
			} catch (tempex) { }

			if (triggerupdate) {
				setTimeout(sendToInside, 600);
			}
		}, 500);

		var tempview = getViewData();
		if (tempview != null && typeof (tempview.type) != "undefined" && tempview.type != null && tempview.type == "orderconfirmed") {
			deferWait(sendToInside, function () {
				var tempconfirm = orderConfirmProcess();
				if (tempconfirm != null && tempconfirm.length > 0) {
					return true;
				}

				return document.readyState != 'loading' && document.readyState != 'interactive';
			});
		}
		else {
			deferWait(sendToInside, function () {
				if (document.readyState != 'loading' && document.readyState != 'interactive') {
					// keepWait(_insideViewUpdate, function () {
					// 	if (!_insideFirstLoad)
					// 		return false;

					// 	if (typeof (_insideGraph) != "undefined" && _insideGraph != null) {
					// 		var temporderdata = getOrderData();

					// 		if (temporderdata != null && temporderdata.length > 0) {
					// 			for (var i = 0; i < temporderdata.length; i++) {
					// 				if (temporderdata[i].action == "trackOrder") {
					// 					if (insideOrderTotal != temporderdata[i].orderTotal) {
					// 						_insideCurPageType = tempcurview.type;
					// 						_insideCurUrl = window.location.href;
					// 						return true;
					// 					}
					// 				}
					// 			}
					// 		}
					// 		else if (insideOrderTotal > 0) {
					// 			insideOrderTotal = 0;
					// 			// return true;
					// 		}

					// 		try {
					// 			var tempcurview = getViewData();
					// 			if (_insideCurUrl != window.location.href) {
					// 				_insideCurUrl = window.location.href;
					// 				_insideCurPageType = tempcurview.type;
					// 				return true;
					// 			}

					// 			if (_insideCurPageType != tempcurview.type) {
					// 				_insideCurPageType = tempcurview.type;
					// 				_insideCurUrl = window.location.href;
					// 				return true;
					// 			}
					// 		} catch (tempex) { }
					// 	}

					// 	return false;
					// });

					// const insideObserver = new MutationObserver(() => {
					// 	try {
					// 		const tempcurview = getViewData();
					// 		if (_insideCurUrl != window.location.href) {
					// 			_insideCurUrl = window.location.href;
					// 			_insideCurPageType = tempcurview.type;
					// 			_insideViewUpdate();
					// 		}

					// 		if (_insideCurPageType != tempcurview.type) {
					// 			_insideCurPageType = tempcurview.type;
					// 			_insideCurUrl = window.location.href;
					// 			_insideViewUpdate();
					// 		}
					// 	} catch (tempex) { }
					// });

					// insideObserver.observe(document.body, {
					// 	childList: true,
					// 	subtree: true
					// });

					deferWait(function () { setTimeout(sendToInside, 600); }, function () {
						var tempconfirm = orderConfirmProcess();
						if (tempconfirm != null && tempconfirm.length > 0) {
							return true;
						}

						return false;
					});

					return true;
				}

				return false;
			});
		}
	}

	if (typeof (_insideGraph) != "undefined" && _insideGraph != null && typeof (_insideGraph.current) != "undefined" && _insideGraph.current != null) {
		processInside(_insideGraph.current);
	}
	else {
		var insideTracker = {
			"action": "getTracker",
			"crossDomain": false,
			"account": insideAccountKey
		};

		try {
			var tempurl = window.location.href.toLowerCase();
			var subsiteMapping = {
				"uk": "1",
				"gb": "1",
				"it": "2",
				"de": "7",
				"fr": "6",
				"es": "8",
				"eu": "9",
				"e1": "9",
				"kw": "16",
				"qa": "17",
				"ae": "18",
				"sa": "19",
				"pl": "98",
				"ch": "99"
			};

			// var temphostname = window.location.hostname.toLowerCase();
			// for (var tempsubsitekey in subsiteMapping) {
			// 	if (subsiteMapping.hasOwnProperty(tempsubsitekey)) {
			// 		if (subsiteMapping[tempsubsitekey] != null) {
			// 			if (temphostname.indexOf(tempsubsitekey) == 0) {
			// 				subsiteId = subsiteMapping[tempsubsitekey];
			// 				break;
			// 			}
			// 		}
			// 	}
			// }

			if (typeof (utag_data) != "undefined" && utag_data != null && utag_data.environmentVersion) {
				var tempinsidecountry = utag_data.environmentVersion.toLowerCase();
				if (subsiteMapping[tempinsidecountry])
					subsiteId = subsiteMapping[tempinsidecountry];
			}

			if (typeof (utag_data) != "undefined" && utag_data != null && utag_data.invoicingCountryForSite) {
				var tempinsidecountry = utag_data.invoicingCountryForSite.toLowerCase();
				if (subsiteMapping[tempinsidecountry])
					subsiteId = subsiteMapping[tempinsidecountry];
			}
		} catch (tempex) { }

		if (typeof (subsiteId) != "undefined" && subsiteId != null)
			insideTracker["subsiteId"] = subsiteId;

		_inside.push(insideTracker);

		_inside.push({
			"action": "bind",
			"name": "onload",
			"callback": function (tracker) {
				if (_insideFirstLoad)
					return;

				_insideJQ = _insideGraph.jQuery;

				processInside(tracker)
			}
		});
		(function (w, d, s, u) {
			a = d.createElement(s), m = d.getElementsByTagName(s)[0];
			a.async = 1;
			a.src = u;
			m.parentNode.insertBefore(a, m);
		})(window, document, "script", "//" + insideTrackerURL + "/ig.js");

		function callEventListener(eventLabel) {
			// The function below will wait until the object insideFrontInterface and the functiong is available
			if (typeof (insideFrontInterface) == "undefined" || insideFrontInterface == null || typeof insideFrontInterface.triggerVisitorEvent == "undefined" || insideFrontInterface.triggerVisitorEvent == null) {
				setTimeout(callEventListener, 1000);
				return;
			}

			insideFrontInterface.triggerVisitorEvent(eventLabel);
		}
	}

})();