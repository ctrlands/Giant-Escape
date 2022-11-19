var CryptoJS = require('crypto-js');

function decrypt(string, code, operation) {
  code = CryptoJS.MD5(code).toString()
  var iv = CryptoJS.enc.Utf8.parse(code.substring(0, 16))
  var key = CryptoJS.enc.Utf8.parse(code.substring(16))
  if (operation) {
      let decrypt = CryptoJS.AES.decrypt(string, key, {
          iv: iv,
          padding: CryptoJS.pad.Pkcs7
      }).toString(CryptoJS.enc.Utf8)
      return decrypt
  }
  let result = CryptoJS.AES.encrypt(string, key, {
      iv: iv,
      mode: CryptoJS.mode.CBC,
      padding: CryptoJS.pad.Pkcs7
  }).toString()
  return result
}