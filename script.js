$("#export-button").click(function () {
	var selectedValues = [];
	$("#subjects :selected").each(function () {
		selectedValues.push($(this).val());
	});
	$.ajax({
    type: 'POST',
    url: '/api/ics',
    data: JSON.stringify({
			section: $("#section option:selected").val(),
			subjects: selectedValues
		}),
    success: function(data) { alert(JSON.stringify(data)); console.log(data); },
    contentType: "application/json",
    dataType: 'json'
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
