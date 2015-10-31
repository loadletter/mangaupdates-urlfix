// ==UserScript==
// @name        Mangaupdates Groups Fix
// @namespace   Mangaupdates Groups Fix (https://github.com/loadletter/mangaupdates-urlfix)
// @description Makes clickable links to scanlators websites
// @match       *://www.mangaupdates.com/groups.html*
// @match       *://www.mangaupdates.com/mylist.html*
// @match       *://www.mangaupdates.com/releases.html*
// @version     1.8
// @downloadURL https://github.com/loadletter/mangaupdates-urlfix/raw/master/mangaupdates_urlfix.user.js
// @updateURL   https://github.com/loadletter/mangaupdates-urlfix/raw/master/mangaupdates_urlfix.user.js
// @grant       none
// ==/UserScript==

if (window.location.pathname === "/mylist.html") {
    set_lastgroup();
} else if (window.location.pathname === "/releases.html") {
    red_lastgroup();
} else if ('id' in get_query_params()) {
    fix_irc();
    fix_url();
    update_groups();
} else {
	set_redirection();
}

function update_groups() {
    var urlfix_groups = document.createElement('script');
    var urlfix_groupshard = parseInt(document.URL.replace(/^.+id=/,'').replace('#', ''), 10) % 20;
    if (urlfix_groupshard !== urlfix_groupshard) {
        return;
    }
    urlfix_groups.type = "text/javascript";
    urlfix_groups.src = "//loadletter.github.io/mangaupdates-urlfix/src/groups/" + urlfix_groupshard + ".js";
    urlfix_groups.onreadystatechange = fix_url;
    urlfix_groups.onload = fix_url;
    urlfix_groups.onerror = fix_url; /* Why not */
    (document.body || document.head || document.documentElement).appendChild(urlfix_groups);
}

function fix_url() {
    var oscript = document.createElement('script');
    oscript.appendChild(document.createTextNode('('+ insertScript +')();'));
    (document.body || document.head || document.documentElement).appendChild(oscript);
}

function fix_irc() {
    var list = document.getElementsByClassName("text");
    var irc='';
    
    for (i=0; i<list.length; i++){
        if(list[i].innerHTML == "<u>IRC</u>") {
            list[i].id = "fixed_irc_url";
            if((irc=list[i].nextSibling.innerHTML) != "<i>No IRC</i>") {
                var a = irc.replace(/^.+@/,'');
                var b = irc.replace('#','').replace(/@.*/,'');
                list[i].nextSibling.innerHTML='<a href="irc://'+a+'/'+b+'"><u>'+a+'/'+b+'</u></a>';
            }
        }
    }
}

function get_query_params() {
    var match, urlParams,
        pl     = /\+/g,
        search = /([^&=]+)=?([^&]*)/g,
        decode = function (s) { return decodeURIComponent(s.replace(pl, " ")); },
        query  = window.location.search.substring(1);

    urlParams = {};
    while (match = search.exec(query))
        urlParams[decode(match[1])] = decode(match[2]);
    
    return urlParams;
}

function set_redirection() {
    var prev_el = document.querySelector('a[href="groups.html?active=false"]');
    if (!prev_el) {
        return;
    }
    var toggle_el = document.createElement('a');
    var redir_key = 'loadletter.urlfix.settings.redirect';
    var toggle_text = function () {
        toggle_el.innerHTML = (typeof(localStorage) !== "undefined" && localStorage.getItem(redir_key)) ? '<u>Do not redirect to website</u>' : '<u>Redirect to group website</u>';
    };
    toggle_text();
    toggle_el.title = "Toggle redirection of mangaupdates group entries to their respective website";
    toggle_el.onclick = function () {
        if (typeof(localStorage) === "undefined") {
            alert("Couldn't save setting, your browser does not support HTML5 localStorage");
            return;
        }
        if (localStorage.getItem(redir_key)) {
            localStorage.removeItem(redir_key);
        } else {
            localStorage.setItem(redir_key, "true");
        }
        toggle_text();
    };
    var parent_el = prev_el.parentElement;
    parent_el.innerHTML = parent_el.innerHTML.replace(/\s+$/, '') + '&nbsp;&nbsp;';
    parent_el.appendChild(toggle_el);
}

function set_lastgroup () {
    var prev_el = document.querySelector('div.low_col1 > a');
    if (!prev_el) {
        return;
    }
    var text_el = document.createTextNode(']\u00a0[');
    var toggle_el = document.createElement('a');
    var redir_key = 'loadletter.urlfix.settings.lastgroup';
    var toggle_text = function () {
        var toggle_hrefs = function (toggled) {
            var latest_chapter = document.querySelectorAll('#list_table span.newlist > a');
            for (var i=0; i<latest_chapter.length; i++) {
                var hr = latest_chapter[i].href.split('#')[0];
                latest_chapter[i].href = toggled ? (hr + '#showLastScanlator') : hr;
            }
        };
        if (typeof(localStorage) !== "undefined" && localStorage.getItem(redir_key)) {
            toggle_hrefs(true);
            toggle_el.innerHTML = '<u>Show all scanlations</u>';
        } else {
            toggle_hrefs(false);
            toggle_el.innerHTML = '<u>Jump to latest scanlation</u>';
        }
    };
    toggle_text();
    toggle_el.title = "Toggles redirection to the scanlator of the last chapter when clicking the link next to the series name";
    toggle_el.onclick = function () {
        if (typeof(localStorage) === "undefined") {
            alert("Couldn't save setting, your browser does not support HTML5 localStorage");
            return;
        }
        if (localStorage.getItem(redir_key)) {
            localStorage.removeItem(redir_key);
        } else {
            localStorage.setItem(redir_key, "true");
        }
        toggle_text();
    };
    prev_el.parentNode.insertBefore(text_el, prev_el.nextSibling);
    text_el.parentNode.insertBefore(toggle_el, text_el.nextSibling);
}

function red_lastgroup () {
    if (!('search' in get_query_params() && window.location.hash === '#showLastScanlator')) {
        return;
    }
    var latest_group = document.querySelector('#main_content a[title="Group Info"][href*="groups.html"]');
    if (latest_group) {
        window.location.href = latest_group.href;
    }
}

/* all the stuff related to the website thing has been moved here,
 * since the groups variable can't be accessed from the usescript */
function insertScript() {
    window.urlfix_groupID = parseInt(document.URL.replace(/^.+id=/,'').replace('#', ''), 10);
    if (window.urlfix_groupID !== window.urlfix_groupID) {
        return;
    }
    var urlfix_local;
    var urlfix_local_name = "loadletter.urlfix.groups." + (window.urlfix_groupID % 20);    
    if(typeof(window.urlfix_grouplist) !== "undefined") {
        window.urlfix_groupSite = window.urlfix_grouplist[String(window.urlfix_groupID)];
        if(typeof(localStorage) !== "undefined") {
            localStorage.setItem(urlfix_local_name, JSON.stringify(window.urlfix_grouplist));
            if (window.urlfix_groupSite !== undefined && localStorage.getItem('loadletter.urlfix.settings.redirect') && /^https?:\/\//.test(window.urlfix_groupSite)) {
                window.location.href = window.urlfix_groupSite;
            }
        }
    } else {
        if(typeof(localStorage) !== "undefined" && (urlfix_local = localStorage.getItem(urlfix_local_name))) {
            window.urlfix_groupSite = JSON.parse(urlfix_local)[window.urlfix_groupID];
            if (window.urlfix_groupSite !== undefined && localStorage.getItem('loadletter.urlfix.settings.redirect') && /^https?:\/\//.test(window.urlfix_groupSite)) {
                window.location.href = window.urlfix_groupSite;
            }
        } else {
            window.urlfix_groupSite = undefined;
        }
    }
    window.urlfix_openSuggBox = function() {
        if(typeof(urlfix_grouplist_shard) === "undefined")
            alert("Could not fetch latest info, the website might be outdated, consider refreshing the page before submitting a new entry");
        var suggboxurl = "http://mufix.herokuapp.com/form?group=" + urlfix_groupID;
        if(urlfix_groupSite !== "undefined")
            suggboxurl += "&update=yes";
        window.open(suggboxurl, '', 'scrollbars=no,resizable=yes, width=700,height=200,status=no,location=no,toolbar=no');
    };
    var urlfix_site_fixed = document.getElementById('fixed_group_url_plus_suggestion');
    var urlfix_site = urlfix_site_fixed || document.createElement('tr');
    urlfix_site.id = "fixed_group_url_plus_suggestion";
    urlfix_site.innerHTML = '<td class="text"><u>Site</u><a href="#" onclick="urlfix_openSuggBox();"> (Suggest an update)</a></td><td class="text">' + (urlfix_groupSite === undefined ? '<i>No Info</i>' : ('<a target="_blank" alt="" href="' + urlfix_groupSite + '"><u>' + urlfix_groupSite + '</u></a>')) + '</td>';
    if(!urlfix_site_fixed) {
        var urlfix_irc_par = document.getElementById("fixed_irc_url").parentNode;
        urlfix_irc_par.parentNode.insertBefore(urlfix_site, urlfix_irc_par.nextSibling);
    }
}

