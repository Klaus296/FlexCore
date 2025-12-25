// cookies.js
export function setCookie(name, value, days = 7) {
  let date = new Date();
  date.setTime(date.getTime() + days * 24 * 60 * 60 * 1000);

  document.cookie =
    encodeURIComponent(name) +
    "=" +
    encodeURIComponent(value) +
    "; expires=" +
    date.toUTCString() +
    "; path=/";
}
// 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
export function getCookie(name) {
  let cookies = document.cookie.split("; ");
  for (let cookie of cookies) {
    let [key, value] = cookie.split("=");
    if (decodeURIComponent(key) === name) {
      return decodeURIComponent(value);
    }
  }
  return null;
}
