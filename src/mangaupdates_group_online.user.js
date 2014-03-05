// ==UserScript==
// @name        Mangaupdates Groups Fix
// @namespace   Mangaupdates Groups Fix (https://github.com/loadletter/mangaupdates-urlfix)
// @match       *://www.mangaupdates.com/groups.html?id=*
// @version     1.6.6
// @downloadURL https://github.com/loadletter/mangaupdates-urlfix/raw/master/mangaupdates_group.user.js
// @updateURL   https://github.com/loadletter/mangaupdates-urlfix/raw/master/mangaupdates_group.meta.js
// @grant       none
// ==/UserScript==

var groupID=document.URL.replace(/^.+id=/,'').replace('#', '');
var groupSite='';


var groupscript = document.createElement('script');
groupscript.type = "text/javascript";
groupscript.src = "https://raw.github.com/loadletter/mangaupdates-urlfix/onlineGroups/src/groups.js";
groupscript.onreadystatechange = run_main_script;
groupscript.onload = run_main_script;
(document.body || document.head || document.documentElement).appendChild(groupscript);

function run_main_script() {
    groupSite=groups[groupID];
     
    var list = document.getElementsByClassName("text");
    var irc='';
    var site = document.createElement('tr');

    /* hack to make suggestionbox work on chrome part 1*/
    var oscript = document.createElement('script');
    oscript.appendChild(document.createTextNode('groupID=' + groupID + ';' + 'groupSite="' + groupSite + '";' + '('+ insertScript +')();'));
    (document.body || document.head || document.documentElement).appendChild(oscript);

    site.innerHTML='<td class="text"><u>Site</u><a href="#" onclick="openSuggBox();"> (Suggest an update)</a></td><td class="text"><a target="_blank" alt="" href="'+groupSite+'"><u>'+groupSite+'</u></a></td>';
    for (i=0; i<list.length; i++){
        if (list[i].innerHTML == "<u>IRC</u>") {
            if((irc=list[i].nextSibling.innerHTML) != "<i>No IRC</i>"){
                var a = irc.replace(/^.+@/,'');
                var b = irc.replace('#','').replace(/@.*/,'');
                list[i].nextSibling.innerHTML='<a href="irc://'+a+'/'+b+'"><u>'+a+'/'+b+'</u></a>';
            }
            if(groupSite!=''){
                insertAfter(list[i].parentNode,site);
            }
        }
    }
}

function insertAfter(referenceNode, newNode) {
    referenceNode.parentNode.insertBefore(newNode, referenceNode.nextSibling);
}

/* hack to make suggestionbox work on chrome part 2*/
function insertScript()
{
	window.openSuggBox = function(){var suggboxurl = "http://mufix.herokuapp.com/form?group=" + groupID; if(groupSite !== "undefined") suggboxurl += "&update=yes"; window.open(suggboxurl, '', 'scrollbars=no,resizable=yes, width=700,height=200,status=no,location=no,toolbar=no');};
}

