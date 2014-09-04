$(function() {
  var btnsGrps;
  btnsGrps = jQuery.trumbowyg.btnsGrps;
  return $('textarea').trumbowyg({
    autogrow: true,
    btns: ['viewHTML', 'formatting', '|', btnsGrps.design, '|', 'link', 'insertImage', btnsGrps.lists]
  });
});
