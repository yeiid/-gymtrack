// main.js

document.addEventListener("DOMContentLoaded", function () {
  // 1. Inicializar tooltips de Bootstrap 5
  if (typeof bootstrap !== "undefined") {
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach((el) => {
      new bootstrap.Tooltip(el);
    });
  }

  // 2. Toggle del icono en "Próximos Vencimientos"
  (function () {
    const header = document.getElementById("proximosVencimientosHeader");
    if (!header) return;
    header.addEventListener("click", function () {
      const icon = this.querySelector(".collapse-icon");
      if (!icon) return;
      const expanded = this.getAttribute("aria-expanded") === "true";
      icon.classList.toggle("fa-rotate-180", !expanded);
    });
  })();

  // 3. Inicializar calendario con FullCalendar (carga diferida)
  (function () {
    let initialized = false;
    function initCalendar() {
      if (initialized) return;
      const el = document.getElementById("calendario");
      if (!el) return;

      // asume window.asistenciasData y window.vencimientosData definidas
      const allEvents = [].concat(
        window.asistenciasData || [],
        window.vencimientosData || []
      );
      const calendar = new FullCalendar.Calendar(el, {
        initialView: "dayGridMonth",
        locale: "es",
        height: "100%",
        headerToolbar: {
          left: "prev,next today",
          center: "title",
          right: "dayGridMonth,timeGridWeek,listWeek",
        },
        themeSystem: "bootstrap",
        events: allEvents,
        lazyFetching: true,
        eventClick: (info) => {
          const title = info.event.title;
          const type = title.startsWith("Vence:")
            ? "Vencimiento"
            : "Asistencia";
          const bg = info.event.backgroundColor;
          const txt = info.event.textColor || "white";
          const date = new Date(info.event.start).toLocaleDateString("es-CO");
          const modalHTML = `
              <div class="modal fade" id="eventInfoModal" tabindex="-1">
                <div class="modal-dialog">
                  <div class="modal-content">
                    <div class="modal-header" style="background-color: ${bg}; color: ${txt}">
                      <h5 class="modal-title">${type}</h5>
                      <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                      <p>${title}</p>
                      <p>Fecha: ${date}</p>
                    </div>
                  </div>
                </div>
              </div>`;
          const wrapper = document.createElement("div");
          wrapper.innerHTML = modalHTML;
          document.body.appendChild(wrapper);
          const modal = new bootstrap.Modal(
            document.getElementById("eventInfoModal")
          );
          modal.show();
          document
            .getElementById("eventInfoModal")
            .addEventListener("hidden.bs.modal", () =>
              document.body.removeChild(wrapper)
            );
        },
        dayMaxEvents: true,
        dayMaxEventRows: 3,
        moreLinkClick: "day",
      });
      calendar.render();
      initialized = true;
    }
    setTimeout(initCalendar, 100);
  })();

  // 4. Búsqueda y filtrado en la tabla de usuarios
  (function () {
    const input = document.getElementById("buscador");
    const table = document.getElementById("tabla-usuarios");
    if (!input || !table) return;

    input.addEventListener("keyup", function () {
      const q = this.value.toLowerCase();
      const rows = table.getElementsByTagName("tr");
      let shown = 0,
        maxShow = 50;

      Array.from(rows).forEach((row) => {
        if (!row.querySelectorAll("td").length) return;
        const text = row.textContent.toLowerCase();
        if (text.includes(q) && shown < maxShow) {
          row.style.display = "";
          shown++;
        } else {
          row.style.display = "none";
        }
      });
    });
  })();

  // 5. Búsqueda y filtrado en el historial de asistencias
  (function () {
    const input = document.getElementById("buscar-historial");
    const tbody = document.querySelector("#tabla-historial tbody");
    if (!input || !tbody) return;

    input.addEventListener("keyup", function () {
      const q = this.value.toLowerCase();
      const rows = tbody.getElementsByTagName("tr");
      let shown = 0,
        maxShow = 50;

      Array.from(rows).forEach((row) => {
        const text = row.textContent.toLowerCase();
        if (text.includes(q) && shown < maxShow) {
          row.style.display = "";
          shown++;
        } else {
          row.style.display = "none";
        }
      });
    });
  })();
});
