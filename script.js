function saveBlob(blob, fileName) {
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

const modal = document.querySelector(".main-modal");
const closeButton = document.querySelectorAll(".modal-close");

const modalClose = () => {
	modal.classList.remove("fadeIn");
	modal.classList.add("fadeOut");
	setTimeout(() => {
		modal.style.display = "none";
	}, 500);
};

const openModal = () => {
	modal.classList.remove("fadeOut");
	modal.classList.add("fadeIn");
	modal.style.display = "flex";
};

for (let i = 0; i < closeButton.length; i++) {
	const elements = closeButton[i];
	elements.onclick = (e) => modalClose();
	window.onclick = function (event) {
		if (event.target == modal) modalClose();
	};
}
