/* ==========================================================================
   SAMHYUP MESH A4 PORTRAIT BROCHURE CONTROLLER
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  const viewport = document.getElementById('viewport');
  const btnZoomIn = document.getElementById('btnZoomIn');
  const btnZoomOut = document.getElementById('btnZoomOut');
  const btnZoomFit = document.getElementById('btnZoomFit');
  const zoomLevelLabel = document.getElementById('zoomLevel');

  let currentZoom = 1.0;

  function updateZoom(newZoom) {
    currentZoom = Math.max(0.4, Math.min(2.0, newZoom));
    viewport.style.transform = `scale(${currentZoom})`;
    if (zoomLevelLabel) {
      zoomLevelLabel.textContent = `${Math.round(currentZoom * 100)}%`;
    }
  }

  if (btnZoomIn) {
    btnZoomIn.addEventListener('click', () => updateZoom(currentZoom + 0.1));
  }
  if (btnZoomOut) {
    btnZoomOut.addEventListener('click', () => updateZoom(currentZoom - 0.1));
  }
  if (btnZoomFit) {
    btnZoomFit.addEventListener('click', () => {
      const availWidth = window.innerWidth - 60;
      const pageWidth = 794;
      const fitScale = Math.min(1.0, availWidth / pageWidth);
      updateZoom(fitScale);
    });
  }

  // Local auto-save for editable text
  const editableElements = document.querySelectorAll('[contenteditable="true"]');
  editableElements.forEach((el, index) => {
    const storageKey = `samhyup_a4_brochure_edit_${index}`;
    const saved = localStorage.getItem(storageKey);
    if (saved) {
      el.innerHTML = saved;
    }
    el.addEventListener('input', () => {
      localStorage.setItem(storageKey, el.innerHTML);
    });
  });

  // Smooth scroll
  document.querySelectorAll('.nav-chip').forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const targetId = link.getAttribute('href');
      const targetEl = document.querySelector(targetId);
      if (targetEl) {
        targetEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  // Initial fit on narrow screen
  if (window.innerWidth < 960) {
    const fitScale = Math.min(1.0, (window.innerWidth - 40) / 794);
    updateZoom(fitScale);
  }
});
