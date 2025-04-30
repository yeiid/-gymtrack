// Función para inicializar la funcionalidad de la página de administración
function initAdminPage(showSQLModal) {
    // Scroll suave para los enlaces de la barra lateral
    const sidebarLinks = document.querySelectorAll('.list-group-item');
    sidebarLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            window.scrollTo({
                top: target.offsetTop - 20,
                behavior: 'smooth'
            });
        });
    });

    // Mostrar modal si es necesario
    if (showSQLModal) {
        new bootstrap.Modal(document.getElementById('modalSQLResults')).show();
    }
} 