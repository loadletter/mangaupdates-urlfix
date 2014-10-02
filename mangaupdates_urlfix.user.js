// ==UserScript==
// @name        Mangaupdates Groups Fix
// @namespace   Mangaupdates Groups Fix (https://github.com/loadletter/mangaupdates-urlfix)
// @description Makes clickable links to scanlators websites
// @match       *://www.mangaupdates.com/groups.html?id=*
// @version     1.6.10
// @downloadURL https://github.com/loadletter/mangaupdates-urlfix/raw/master/mangaupdates_urlfix.user.js
// @updateURL   https://github.com/loadletter/mangaupdates-urlfix/raw/master/mangaupdates_urlfix.user.js
// @grant       none
// ==/UserScript==

fix_irc();
inject_groups();

function inject_groups() {
    var urlfix_groups = document.createElement('script');
    var urlfix_groupshard = parseInt(document.URL.replace(/^.+id=/,'').replace('#', '')) % 20 || 0; /* magic value */
    urlfix_groups.type = "text/javascript";
    urlfix_groups.src = "//loadletter.github.io/mangaupdates-urlfix/src/groups/" + urlfix_groupshard + ".js";
    urlfix_groups.onreadystatechange = fix_url;
    urlfix_groups.onload = fix_url;
    (document.body || document.head || document.documentElement).appendChild(urlfix_groups);
}

function fix_url() {
    /* hack to make suggestionbox work on chrome part 1*/
    var oscript = document.createElement('script');
    oscript.appendChild(document.createTextNode('('+ insertScript +')();'));
    (document.body || document.head || document.documentElement).appendChild(oscript);
}

function fix_irc() {
    var list = document.getElementsByClassName("text");
    var irc='';
    
    for (i=0; i<list.length; i++){
        if (list[i].innerHTML == "<u>IRC</u>") {
            list[i].id = "fixed_irc_url";
            if((irc=list[i].nextSibling.innerHTML) != "<i>No IRC</i>") {
                var a = irc.replace(/^.+@/,'');
                var b = irc.replace('#','').replace(/@.*/,'');
                list[i].nextSibling.innerHTML='<a href="irc://'+a+'/'+b+'"><u>'+a+'/'+b+'</u></a>';
            }
        }
    }
}

/* hack to make suggestionbox work on chrome part 2 */

/* all the stuff related to the website thing has been moved here,
 * since the groups variable can't be accessed from the usescript */
function insertScript() {
    window.urlfix_groupID = document.URL.replace(/^.+id=/,'').replace('#', '');
    window.urlfix_groupSite = window.urlfix_grouplist[window.urlfix_groupID];
    window.urlfix_openSuggBox = function(){var suggboxurl = "http://mufix.herokuapp.com/form?group=" + urlfix_groupID; if(urlfix_groupSite !== "undefined") suggboxurl += "&update=yes"; window.open(suggboxurl, '', 'scrollbars=no,resizable=yes, width=700,height=200,status=no,location=no,toolbar=no');};
    var urlfix_site_fixed = document.getElementById('fixed_group_url_plus_suggestion');
    var urlfix_site = urlfix_site_fixed || document.createElement('tr');
    urlfix_site.id = "fixed_group_url_plus_suggestion";
    urlfix_site.innerHTML = '<td class="text"><u>Site</u><a href="#" onclick="urlfix_openSuggBox();"> (Suggest an update)</a></td><td class="text">' + (urlfix_groupSite === undefined ? '<u>No Info</u>' : ('<a target="_blank" alt="" href="' + urlfix_groupSite + '"><u>' + urlfix_groupSite + '</u></a>')) + '</td>';
    if(!urlfix_site_fixed) {
        var urlfix_irc_par = document.getElementById("fixed_irc_url").parentNode;
        urlfix_irc_par.parentNode.insertBefore(urlfix_site, urlfix_irc_par.nextSibling);
    }
}

