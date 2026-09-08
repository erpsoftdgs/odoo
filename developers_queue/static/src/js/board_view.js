console.log('load complete');
const el = document.querySelector("a.nav-link[href='/web/login']");
if (el) {
    el.setAttribute('href', '/developer/logout');
    el.innerHTML = '<b>Logout</b>';
}
Array.from(document.querySelectorAll("tr[data-href]")).forEach(el => {
    console.log('here', el);
    el.addEventListener('click', (e) => {
        console.log('clicked')
        location.href = el.getAttribute('data-href');
    });
});
