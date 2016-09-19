// Various ready-made functions for grammars using JavaScript

var helper = {
	// ArrayBuffer to String
	ab2str: function (buf) {
	  return String.fromCharCode.apply(null, new Uint8Array(buf));
	},

	// String to ArrayBuffer
	str2ab: function (str) {
		var buf = new ArrayBuffer(str.length), 
			bufView = new Uint8Array(buf);
		for (var i=0, strLen=str.length; i<strLen; i++) {
			bufView[i] = str.charCodeAt(i);
		}
		return buf;
	},

	// ArrayBufferView to Hex
	abv2hex: function (abv) {
	    var b = new Uint8Array(abv.buffer, abv.byteOffset, abv.byteLength),
	    	hex = "";
	    for (var i=0; i<b.length; ++i) {
	        var zeropad = (b[i] < 0x10) ? "0" : "";
	        hex += zeropad + b[i].toString(16);
	    }
	    return hex;
	},
	
	// Hex to ArrayBufferView
	hex2abv: function (hex) {
	    if (hex.length % 2 !== 0) {
	      hex = "0" + hex;
	    }

	    var abv = new Uint8Array(hex.length / 2);
	    for (var i=0; i<abv.length; ++i) {
	      abv[i] = parseInt(hex.substr(2*i, 2), 16);
	    }
	    return abv;
	},

	// Base64 to Hex
	b642hex: function(str) {
	    var bin = window.atob(str.replace(/-/g, "+").replace(/_/g, "/"));
	    var res = "";
	    for (var i = 0; i < bin.length; i++) {
	        res += ("0" + bin.charCodeAt(i).toString(16)).substr(-2);
	    }
	    return res;
	},

	// Hex to Base64
	hex2b64: function(hex) {
	    var bin = "";
	    for (var i = 0; i < hex.length; i += 2) {
	        bin += String.fromCharCode(parseInt(hex.substr(i, 2), 16));
	    }
	    return window.btoa(bin).replace(/=/g, "").replace(/\+/g, "-").replace(/\//g, "_");
	}
};
