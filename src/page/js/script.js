for (const element of document.getElementsByClassName("open"))
  element.href = "/finished?open=" + encodeURIComponent(element.href);
