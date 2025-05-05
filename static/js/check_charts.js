/**
 * Script de verificación de Chart.js
 * Este script verifica que las bibliotecas de gráficos estén disponibles
 * y registra la versión y configuración en la consola para diagnóstico.
 */
document.addEventListener('DOMContentLoaded', function() {
  console.log('Verificando bibliotecas de gráficos...');
  
  // Comprobar si Chart.js está disponible
  if (typeof Chart !== 'undefined') {
    console.log('✅ Chart.js disponible. Versión:', Chart.version);
    
    // Verificar plugin datalabels
    if (typeof ChartDataLabels !== 'undefined') {
      console.log('✅ Plugin ChartDataLabels disponible');
    } else {
      console.error('❌ Plugin ChartDataLabels no disponible');
    }
    
    // Información para solución de problemas
    console.log('Información del navegador:', navigator.userAgent);
    console.log('Soporte de canvas:', !!document.createElement('canvas').getContext);
    
    // Verificar existencia de los archivos locales
    const chartFiles = [
      '/static/js/vendor/chart.min.js',
      '/static/js/vendor/chartjs-plugin-datalabels.min.js'
    ];
    
    chartFiles.forEach(file => {
      fetch(file)
        .then(response => {
          if (response.ok) {
            console.log(`✅ Archivo ${file} accesible`);
          } else {
            console.error(`❌ Archivo ${file} no accesible (${response.status})`);
          }
        })
        .catch(error => {
          console.error(`❌ Error al verificar archivo ${file}:`, error);
        });
    });
  } else {
    console.error('❌ Chart.js no está disponible');
  }
}); 