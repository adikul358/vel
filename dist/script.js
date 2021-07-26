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

const modal = document.querySelectorAll(".modal");
const importModal = document.querySelector(".import-modal");
const integrationModal = document.querySelector(".integration-modal");
const importCloseButton = document.querySelectorAll(".import-modal-close");
const integrationCloseButton = document.querySelectorAll(
	".integration-modal-close"
);

const modalClose = (e) => {
	e.classList.remove("fadeIn");
	e.classList.add("fadeOut");
	setTimeout(() => {
		e.style.display = "none";
	}, 500);
};

const openImportModal = () => {
	importModal.classList.remove("fadeOut");
	importModal.classList.add("fadeIn");
	importModal.style.display = "flex";
};

const openIntegrationModal = () => {
	integrationModal.classList.remove("fadeOut");
	integrationModal.classList.add("fadeIn");
	integrationModal.style.display = "flex";
};

for (let i = 0; i < importCloseButton.length; i++) {
	const elements = importCloseButton[i];
	elements.onclick = (e) => modalClose(importModal);
}

for (let i = 0; i < integrationCloseButton.length; i++) {
	const elements = integrationCloseButton[i];
	elements.onclick = (e) => modalClose(integrationModal);
}

window.onclick = function (event) {
	if (event.target == importModal) modalClose(importModal);
	if (event.target == integrationModal) modalClose(integrationModal);
};