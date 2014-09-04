$ ->
	btnsGrps = jQuery.trumbowyg.btnsGrps
	$('textarea').trumbowyg
		autogrow: true
		btns: ['viewHTML',
           'formatting',
           '|', btnsGrps.design,
           '|', 'link',
			'insertImage',
        	btnsGrps.lists,]
		# resetCss: true
		# btns: ['bold', 'italic', '|', 'insertImage']
		# closable: true
