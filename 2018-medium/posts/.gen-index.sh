awk '
/<title>/{
 sub(/^.*<title>/,"")
 sub(/<.title>.*/,"")
 title=$0
 date=FILENAME
 sub(/_.*/,"",date)
 print "<p>"date" <a href="q FILENAME q">"title"</a>"
}
' q="'" 20*.html | sort -r > index.html
for i in *.html
do
 #sed -i -e "s?<pre ?<code ?g" -e "s?</pre>?</code>?g" $i
 #sed -i -e "s?<pre [^>]*>?<pre>?g" $i
 #sed -i -e "s?<pre[^>]*>?<code>?g" -e "s?</pre>?</code>?g" $i
 sed -i -e "s?font-family:.*?<!--&-->?g" $i
done
