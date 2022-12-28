


file="2013-2018/12c-access-control-lists/index.html"

for file in 2013-2018/*/index.html
do
awk '
# for dbi blogs
/This was first published on/{
link=gensub(/This was first published on .*>(.*)<.* [(](....)-(..)-(..)[)].*/,"\\1",1)
yyyy=gensub(/This was first published on .*>(.*)<.* [(](....)-(..)-(..)[)].*/,"\\2",1)
mm=  gensub(/This was first published on .*>(.*)<.* [(](....)-(..)-(..)[)].*/,"\\3",1)
dd=  gensub(/This was first published on .*>(.*)<.* [(](....)-(..)-(..)[)].*/,"\\4",1)
dir=yyyy"/"mm"/"dd
if ( dir ~ "^201" ) system( "mkdir -p " dir)
$0="<p class=firstpub>"$0", republishing for new followers. The content is related to the the versions available at the publication date</p>"
}
dir =="" { exit }
/.*<h1 class="entry-title">(.*)<[/]h1>.*/{
 title=gensub(/.*<h1 class="entry-title">(.*)<[/]h1>.*/,"\\1",1)
}
#
{
body=body"\n"$0
}
END{
print "<html><head>\n<link rel=canonical href="link" />\n<meta name=description content="q"A blog post from "yyyy " about " title q ">\n<title>"title"</title>\n<link rel=stylesheet href=../../../style.css media=all>   "head"\n</head><body>\n"body"\n</body></html>" > dir "/" name ".html"
print dir "/" name ".html" , link > "/dev/stderr"
}
' body='
<p class=aboutme>
<br/>
<table width=100%>
<tr>
<td>
<a href=https://linkedin.com/in/franckpachot>Linkedin</a>, <a href=https://twitter.com/franckpachot>Twitter</a>, <a href=https://www.youtube.com/@franckpachot/community>Youtube</a>, <a href=https://mastodon.social/@FranckPachot>Mastodon</a>, <a href=https://dev.to/franckpachot>dev.to</a>
</td><td>
<img src=https://res.cloudinary.com/practicaldev/image/fetch/s--h5Lx9WjS--/c_fill,f_auto,fl_progressive,h_320,q_auto,w_320/https://dev-to-uploads.s3.amazonaws.com/uploads/user/profile_image/114176/c569c0db-9431-4319-ae0b-cb5aa7c7d0e3.png height=100 width=100/>
</td>
</tr>
</table>
<br/>
</p>
' head='
' q="'" name=$(basename $(dirname "$file")) "$file"
done
