function deleteNote(noteId) {
  fetch("/delete-note", {
    method: "POST",
    body: JSON.stringify({ noteId: noteId }),
  }).then((_res) => {
    window.location.href = "/";
  //      window.location.href = "/simulation/";
    return false;
  });
}

function deleteRecord(recordId) {
  fetch("/delete-record", {
    method: "POST",
    body: JSON.stringify({ recordId: recordId }),
  }).then((_res) => {
    window.location.href = "/simulation";
    return false;
  });
}
