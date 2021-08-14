// API

const saveBlob = (blob, fileName) => {
	var a = document.createElement('a');
	a.href = window.URL.createObjectURL(blob);
	a.download = fileName;
	a.dispatchEvent(new MouseEvent('click'));
}

$.ajax({
	type: 'POST',
	url: '/api/tts',
	success: function (data) {
		data.data.forEach(function (ttDate) {
			$("#timetable").append(`<option value="${ttDate}">${ttDate}</option>`)
		})
		console.log(data);
	},
	contentType: "application/json",
	dataType: 'json'
});

$("#export-button").click(function () {
	var selectedValues = [];
	$("#subjects :selected").each(function () {
		selectedValues.push($(this).val());
	});
	payload = JSON.stringify({
		date: $("#timetable option:selected").val(),
		section: $("#section option:selected").val(),
		subjects: selectedValues
	})
	var xhr = new XMLHttpRequest();
	xhr.open('POST', '/api/ics', true);
	xhr.setRequestHeader('Content-Type', 'application/json');
	xhr.responseType = 'blob';
	xhr.onload = function (e) {
		var blob = e.currentTarget.response;
		var contentDispo = e.currentTarget.getResponseHeader('Content-Disposition');
		var fileName = contentDispo.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)[1];
		saveBlob(blob, fileName);
	}
	xhr.send(payload);
});




// UI


const closeModal = (e) => {
	e.removeClass("fadeIn");
	e.addClass("fadeOut");
	setTimeout(() => {
		e.removeClass("flex");
		e.addClass("hidden");
	}, 500);
};

const openModal = (e) => {
	e.removeClass("hidden");
	e.addClass("flex");
	e.removeClass("fadeOut");
	e.addClass("fadeIn");
	e.css("display", "flex")
};

jQuery(document).ready(function(){ 

	const importModal = $(".import-modal")
	const integrationModal = $(".integration-modal");
	
	$(".import-modal-close").click(() => closeModal(importModal));
	$(".integration-modal-close").click(() => closeModal(integrationModal));
	
	window.onclick = function (event) {
		if (event.target == importModal[0]) closeModal(importModal);
		if (event.target == integrationModal[0]) closeModal(integrationModal);
	};
	
	$("#integration-button").click(function () {
		var subjectsStr = "";
		$("#subjects :selected").each(function () {
			subjectsStr += $(this).html() + ", ";
		});
		subjectsStr = subjectsStr.substring(0, subjectsStr.length - 2);
	
		$("#integration-section").html($("#section :selected").val());
		$("#integration-subjects").html(subjectsStr);
	});

	$("#googleSignInButton").hover(function () {
		$(this).attr("src", "btn_google_hover.png");
	}, function () {
		$(this).attr("src", "btn_google.png");
	});
	$("#googleSignInButton").mousedown(function () {
		$("#googleSignInButton").attr("src", "btn_google_active.png");
	});
	$("#googleSignInButton").mouseup(function () {
		$("#googleSignInButton").attr("src", "btn_google_hover.png");
	});
})