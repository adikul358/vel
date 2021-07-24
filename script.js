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
	$.ajax({
		type: 'POST',
		url: '/api/ics',
		cache: false,
		xhr: function () {
			var xhr = new XMLHttpRequest();
			xhr.onreadystatechange = function () {
				if (xhr.readyState == 2) {
					if (xhr.status == 200) {
						xhr.responseType = "blob";
					} else {
						xhr.responseType = "text";
					}
				}
			};
			xhr.send(JSON.stringify({
				date: $("#timetable option:selected").val(),
				section: $("#section option:selected").val(),
				subjects: selectedValues
			}))
			return xhr;
		},
		success: function (data) {
			var blob = new Blob([data], { type: "application/octetstream" });
			var isIE = false || !!document.documentMode;
			if (isIE) {
				window.navigator.msSaveBlob(blob, fileName);
			} else {
				var url = window.URL || window.webkitURL;
				link = url.createObjectURL(blob);
				var a = $("<a />");
				a.attr("download", fileName);
				a.attr("href", link);
				$("body").append(a);
				a[0].click();
				$("body").remove(a);
			}
		}
	});
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
