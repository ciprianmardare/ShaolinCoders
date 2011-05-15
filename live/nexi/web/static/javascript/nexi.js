/* No Conflict. Just in case */
jQuery.noConflict();

/* Homepage slideshow */
jQuery(function($){
	$('#slideshow').cycle({
		pager: '#pager',
		fx: 'fade',
		easing: 'swing',
		speed: 1200,
		timeout: 3600
	});
});

/* All Related to Name and Skills */
jQuery(function($){

if (document.getElementById('edit-project')) {

	var $skillList = $('#skill-list'),		
		$addForm = $('#add-skill'),
		$editForm = $('#edit-project'),
		$editSkill = $('input[name=skills]', $editForm),
		$editName = $('input[name=name]', $editForm),
		$text = $(':text', $addForm),
		skills = $editSkill.val().split(','),
		$projectName = $('#project-name'),
		projectName = $('input',$projectName);
		
	/* Add Skill */
	$addForm.bind('submit', function(e){
		if ($text.val() !== '') {
			$('<li>'+$text.val()+'</li>').appendTo($skillList);
			skills.push($text.val());
			$text.val('');
			updateSkills();
		}
		return false;
	});
	
	/* Delete Skill */
	$skillList
	.bind('mouseover', function(e){
		if ($(e.target).is('li')){
			$(e.target).addClass('delete');
		}
	})
	.bind('mouseout', function(e){
		if ($(e.target).is('li')){
			$(e.target).removeClass('delete');
		}
	})
	.bind('click', function(e){
		if ($(e.target).is('.delete')){
			$(e.target).remove();
			skills.splice(skills.indexOf($(e.target).text()), 1);
			updateSkills();				
		}
	});
	
	/* Edit Title */
	$projectName.click(function(){
		if (!$(this).is('.edit')){
			$(this).addClass('edit');
		}
	}).bind('keyup', function(e){
		if (e.keyCode === 13) {
			$(this).removeClass('edit');
			$('span', $projectName).text($(e.target).val());
			projectName.val($(e.target).val());
			updateSkills();
		}
	});
	
	/* Ajax Update Name & Project Skills */
	function updateSkills(){
		$editSkill.val(skills.join(','));
		$editName.val(projectName.val());
		$.ajax({
			url: $editForm.attr('action'),
			type: 'POST',
			data: $editForm.serialize(),
			success: function(data){
				$('#fetch').click(); /*Getting Suggestions*/
 			}
		});	
	}
	
}
	
});

/*
 * Delete Project
 */
jQuery(function($){
	$('#delete-project').click(function(){
		return confirm('Are you sure you want to delete '+$(this).attr('data-name')+' ?');
	});
});

/*
 * Fetch Suggestions
 */
jQuery(function($){
	
	var $button = $('#fetch'),
		$results = $('#results');
		
	$button.click(function(){
		$.ajax({
			url: $button.data('url'),
			data: $button.data('data'),
			success: function(data){
				$results.html(data);
				//Updating the score
				updateScore();
				
				//Get github data
				//We should cache these somehow
				getYQLgithub();
			}
		});
	}).trigger('click');
});

/*
 * Add & Remove Person to Staff
 */
jQuery(function($){
	
	var $suggestions = $('#results'),
		$staff = $('#staff');
	
	/* Add */
	$suggestions.click(function(e){
		if ($(e.target).is('.add-to-staff')){
			var $person = $(e.target).parents('.person');
			$person.appendTo($staff);
			var params = 'project_id=' + $('#project-name').data('id') + '&url=' + $person.data('url');
			$.ajax({
				url: '/member/add',
				type: 'GET',
				data: params,
				success: function(data){
				  updateScore();
				}
			});
			return false;
		}
	});

	/* Remove */
	$staff.click(function(e){
		if ($(e.target).is('.remove-from-staff')){
			var $person = $(e.target).parents('.person');
			var params = 'project_id=' + $('#project-name').data('id') + '&url=' + $person.data('url')
			$.ajax({
				url: '/member/delete',
				data: params,
				type: 'GET',
				success: function(data){
			    $('#fetch').click(); /*Getting Suggestions*/
			  }
			});
			updateScore();
			$person.remove();
			return false;
		}
	});
	
	if (document.getElementById('staff')) {
	
		/* Load inital Staff */
		$.ajax({
			url: '/ajax/members/',
			data: 'project_id='+$('#project-name').data('id'),
			type: 'GET',
			success: function(data){
				$staff.html(data);	
			}
		});
	
	}

});

/*
 * Score
 */
function updateScore(){
	(function($) {
		$.ajax({
			url: '/ajax/score',
			data: 'project_id='+$('#project-name').data('id'),
			type: 'GET',
			success: function(data){
				$('#completed-percent').text(data);
			}
		});
	})(jQuery)
}

/*
 * Github Profile with YQL
 */
function getYQLgithub(){
	(function($) {		
		var $person = $('#results .person');		
		$person.each(function(){
			var $el = $(this);
			$.ajax({
				url: '/ajax/profiles',
				data: 'linkedin_profile='+$el.data('url'),
				success: function(data){
					if (data !== '') {
						$('.person-skills', $el).after('<div class="github"><a href="'+data+'">github</a></div>');
					}
				}
			});
		});
			
		
	})(jQuery);
}
