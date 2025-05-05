/**
 * Módulo de gráficos financieros para GymTrack
 * Desarrollado por: NEURALJIRA_DEV - YEIFRAN HERNANDEZ
 * 
 * Este archivo contiene la lógica para los gráficos financieros utilizados
 * en el módulo de finanzas del sistema GymTrack.
 */

// Función para cargar scripts de forma secuencial
function loadScript(src, integrity, callback) {
  const script = document.createElement('script');
  script.src = src;
  if (integrity) {
    script.integrity = integrity;
    script.crossOrigin = 'anonymous';
  }
  script.async = true;
  
  // Añadir información de depuración a la consola
  console.log(`Intentando cargar script: ${src}`);
  
  // Manejar evento de carga exitosa
  script.onload = function() {
    console.log(`Script cargado exitosamente: ${src}`);
    if (callback) callback();
  };
  
  // Manejar error de carga
  script.onerror = function(error) {
    console.error(`Error al cargar script: ${src}`, error);
    
    // Si el error es con un CDN, intentar ruta alternativa
    if (src.includes('cdn.jsdelivr.net')) {
      console.log('Intentando fuente alternativa de CDN...');
      loadScript(src.replace('cdn.jsdelivr.net', 'cdnjs.cloudflare.com/ajax/libs'), null, callback);
    } 
    // Si es una ruta local que no se encuentra, intentar cargar desde CDN como respaldo
    else if (src.startsWith('/static/')) {
      console.log('Archivo local no encontrado, intentando desde CDN...');
      if (src.includes('chart.min.js')) {
        loadScript('https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js', null, callback);
      } else if (src.includes('datalabels')) {
        loadScript('https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.0.0', null, callback);
      } else {
        mostrarErrorGraficos();
      }
    } else {
      console.error('No se pudo cargar el script después de intentar alternativas');
      mostrarErrorGraficos();
    }
  };
  
  document.head.appendChild(script);
}

// Mostrar mensaje de error cuando no se pueden cargar las gráficas
function mostrarErrorGraficos() {
  document.querySelectorAll('canvas[id^="grafico"]').forEach(canvas => {
    const container = canvas.parentElement;
    canvas.style.display = 'none';
    
    const errorMsg = document.createElement('div');
    errorMsg.className = 'alert alert-warning my-3';
    errorMsg.innerHTML = `
      <strong>No se pudieron cargar las gráficas.</strong><br>
      Posibles soluciones:
      <ul>
        <li>Intente recargar la página (presione F5)</li>
        <li>Verifique su conexión a internet</li>
        <li>Si el problema persiste, notifique al administrador del sistema</li>
      </ul>
      <small class="d-block mt-2">Detalles técnicos: Error al cargar las bibliotecas de gráficos JavaScript.</small>
    `;
    container.appendChild(errorMsg);
    
    // Añadir también un botón para reintentar la carga
    const reintentarBtn = document.createElement('button');
    reintentarBtn.className = 'btn btn-sm btn-outline-primary mt-2';
    reintentarBtn.innerHTML = '<i class="fas fa-sync-alt me-1"></i>Reintentar';
    reintentarBtn.onclick = function() {
      // Remover los mensajes de error
      container.querySelectorAll('.alert').forEach(el => el.remove());
      // Mostrar canvas nuevamente
      canvas.style.display = 'block';
      // Reintentar la inicialización
      inicializarFinanzasCharts();
    };
    container.appendChild(reintentarBtn);
  });
  
  // Registrar el error en la consola para diagnóstico
  console.error("Error al cargar las gráficas financieras. Verifique las conexiones a CDN o archivos locales.");
}

// Función para formatear moneda colombiana
function formatoCOP(valor) {
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(valor);
}

// Función para parsear JSON de manera segura y sanitizar los datos
function parseJsonSafe(jsonString, defaultValue = []) {
  try {
    // Si la cadena JSON está vacía o no es válida, usar valor predeterminado
    if (!jsonString || jsonString === 'null' || jsonString === 'undefined' || jsonString === '[]') {
      console.warn("JSON string vacío o no válido:", jsonString);
      return defaultValue;
    }
    
    // Reemplazar valores problemáticos
    const cleanedString = jsonString
      .replace(/NaN/g, 'null')
      .replace(/Infinity/g, 'null')
      .replace(/-Infinity/g, 'null')
      .replace(/None/g, 'null');
    
    // Intentar parsear JSON
    try {
      const parsedData = JSON.parse(cleanedString);
      
      // Verificar si es array y sanitizar valores
      if (Array.isArray(parsedData)) {
        return parsedData.map(item => {
          // Convertir null, undefined o NaN a 0
          if (item === null || item === undefined || 
              (typeof item === 'number' && (isNaN(item) || !isFinite(item)))) {
            return 0;
          }
          return item;
        });
      }
      return parsedData;
    } catch (parseError) {
      console.error("Error al parsear JSON:", parseError, "String original:", jsonString);
      return defaultValue;
    }
  } catch (error) {
    console.error("Error general al procesar JSON:", error);
    return defaultValue;
  }
}

// Función para crear gráficos de forma segura
function crearGraficoSeguro(id, tipo, configuracion) {
  try {
    const elemento = document.getElementById(id);
    if (!elemento) {
      console.error(`Elemento con ID "${id}" no encontrado`);
      return null;
    }
    
    // Validar configuración antes de crear el gráfico
    if (!configuracion || !configuracion.data || !configuracion.data.datasets) {
      console.error(`Configuración inválida para gráfico ${id}`);
      return null;
    }
    
    // Validar que todos los datasets tienen datos válidos
    configuracion.data.datasets.forEach(dataset => {
      if (!Array.isArray(dataset.data)) {
        console.error(`Datos inválidos en dataset para gráfico ${id}`);
        dataset.data = [0];
      }
      // Convertir cualquier valor no numérico a 0
      dataset.data = dataset.data.map(val => {
        return (val === null || val === undefined || isNaN(val) || !isFinite(val)) ? 0 : val;
      });
    });
    
    console.log(`Creando gráfico ${tipo} en ${id}`);
    return new Chart(elemento.getContext('2d'), configuracion);
  } catch (error) {
    console.error(`Error al crear gráfico ${tipo} en ${id}:`, error);
    
    // Mostrar mensaje de error en lugar del gráfico
    const canvas = document.getElementById(id);
    if (canvas) {
      const container = canvas.parentElement;
      canvas.style.display = 'none';
      
      const errorMsg = document.createElement('div');
      errorMsg.className = 'alert alert-danger my-2';
      errorMsg.innerHTML = `<strong>Error al crear gráfico:</strong> ${error.message}`;
      container.appendChild(errorMsg);
    }
    
    return null;
  }
}

// Configurar los colores corporativos consistentes
const COLORES = {
  membresias: {
    bg: 'rgba(59, 130, 246, 0.6)',
    border: 'rgb(59, 130, 246)'
  },
  productos: {
    bg: 'rgba(16, 185, 129, 0.6)',
    border: 'rgb(16, 185, 129)'
  },
  margenes: {
    bg: 'rgba(249, 115, 22, 0.2)',
    border: 'rgb(249, 115, 22)'
  },
  neto: {
    bg: 'rgba(139, 92, 246, 0.6)',
    border: 'rgb(139, 92, 246)'
  },
  planes: [
    'rgba(59, 130, 246, 0.8)',  // Azul
    'rgba(16, 185, 129, 0.8)',  // Verde
    'rgba(249, 115, 22, 0.8)',  // Naranja
    'rgba(139, 92, 246, 0.8)',  // Morado
    'rgba(236, 72, 153, 0.8)',  // Rosa
    'rgba(75, 85, 99, 0.8)'     // Gris
  ]
};

// Función principal para inicializar todos los gráficos
function inicializarGraficos() {
  try {
    console.log('Inicializando gráficos financieros profesionales...');
    
    // Registrar el plugin de datalabels si está disponible
    if (typeof ChartDataLabels !== 'undefined') {
      Chart.register(ChartDataLabels);
    }
    
    // Obtener datos con validación y valores por defecto
    try {
      var meses = parseJsonSafe(document.getElementById('datos-meses').value, ["Ene", "Feb", "Mar", "Abr", "May", "Jun"]);
      var datosIngresosMembresias = parseJsonSafe(document.getElementById('datos-ingresos-membresias').value, [0, 0, 0, 0, 0, 0]);
      var datosIngresosProductos = parseJsonSafe(document.getElementById('datos-ingresos-productos').value, [0, 0, 0, 0, 0, 0]);
      var datosMargenes = parseJsonSafe(document.getElementById('datos-margenes').value, [0, 0, 0, 0, 0, 0]);
      var datosIngresosNetos = parseJsonSafe(document.getElementById('datos-ingresos-netos').value, [0, 0, 0, 0, 0, 0]);
      var planesNombres = parseJsonSafe(document.getElementById('datos-planes-nombres').value, ["Sin datos"]);
      var datosPlanes = parseJsonSafe(document.getElementById('datos-planes').value, [1]);
      var ingresosPotencialesPlanes = parseJsonSafe(document.getElementById('datos-ingresos-potenciales-plan').value, [0]);
      var productosNombres = parseJsonSafe(document.getElementById('datos-productos-nombres').value, ["Sin ventas"]);
      var productosCantidades = parseJsonSafe(document.getElementById('datos-productos-cantidades').value, [0]);
      var productosIngresos = parseJsonSafe(document.getElementById('datos-productos-ingresos').value, [0]);
      var productosMargenes = parseJsonSafe(document.getElementById('datos-productos-margenes').value, [0]);
    } catch (e) {
      console.error("Error al obtener datos JSON:", e);
      var meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun"];
      var datosIngresosMembresias = [0, 0, 0, 0, 0, 0];
      var datosIngresosProductos = [0, 0, 0, 0, 0, 0];
      var datosMargenes = [0, 0, 0, 0, 0, 0];
      var datosIngresosNetos = [0, 0, 0, 0, 0, 0];
      var planesNombres = ["Sin datos"];
      var datosPlanes = [1];
      var ingresosPotencialesPlanes = [0];
      var productosNombres = ["Sin ventas"];
      var productosCantidades = [0];
      var productosIngresos = [0];
      var productosMargenes = [0];
    }
    
    // Calcular totales para proporciones
    const totalIngresos = datosIngresosMembresias.reduce((a, b) => a + b, 0) + 
                         datosIngresosProductos.reduce((a, b) => a + b, 0);
    
    // Verificar que Chart.js está disponible
    if (typeof Chart === 'undefined') {
      console.error('Chart.js no está disponible. No se pueden crear gráficos.');
      mostrarErrorGraficos();
      return;
    }

    // Gráfico de ingresos y márgenes (financiero histórico)
    try {
      crearGraficoSeguro('graficoIngresos', 'bar', {
        type: 'bar',
        data: {
          labels: meses,
          datasets: [
            {
              label: 'Ingresos por Membresías',
              data: datosIngresosMembresias,
              backgroundColor: COLORES.membresias.bg,
              borderColor: COLORES.membresias.border,
              borderWidth: 1,
              order: 1
            },
            {
              label: 'Ingresos por Productos',
              data: datosIngresosProductos,
              backgroundColor: COLORES.productos.bg,
              borderColor: COLORES.productos.border,
              borderWidth: 1,
              order: 1
            },
            {
              label: 'Ingresos Netos',
              data: datosIngresosNetos,
              type: 'line',
              backgroundColor: COLORES.neto.bg,
              borderColor: COLORES.neto.border,
              borderWidth: 2,
              tension: 0.4,
              pointRadius: 4,
              pointBackgroundColor: COLORES.neto.border,
              fill: false,
              order: 0
            },
            {
              label: 'Margen de Ganancia',
              data: datosMargenes,
              type: 'line',
              backgroundColor: COLORES.margenes.bg,
              borderColor: COLORES.margenes.border,
              borderWidth: 2,
              borderDash: [5, 5],
              tension: 0.1,
              pointRadius: 3,
              pointBackgroundColor: COLORES.margenes.border,
              fill: false,
              order: 0
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'top',
              align: 'center',
              labels: {
                boxWidth: 12,
                usePointStyle: true
              }
            },
            tooltip: {
              mode: 'index',
              intersect: false,
              callbacks: {
                label: function(context) {
                  let value = context.parsed.y;
                  if (isNaN(value)) value = 0;
                  return context.dataset.label + ': ' + formatoCOP(value);
                }
              }
            },
            datalabels: {
              display: function(context) {
                // Solo mostrar valores para los últimos dos meses
                return context.dataIndex >= context.dataset.data.length - 2;
              },
              color: function(context) {
                return context.dataset.borderColor;
              },
              font: {
                weight: 'bold',
                size: 10
              },
              formatter: function(value) {
                if (value < 1000) return '';
                return formatoCOP(value).replace('COP', '').trim();
              },
              anchor: 'end',
              align: 'top',
              offset: 0
            }
          },
          scales: {
            x: {
              grid: {
                display: false
              }
            },
            y: {
              beginAtZero: true,
              ticks: {
                callback: function(value) {
                  return formatoCOP(value);
                }
              },
              grid: {
                borderDash: [2, 2]
              }
            }
          },
          interaction: {
            mode: 'index',
            intersect: false
          }
        }
      });
    } catch (e) {
      console.error("Error en gráfico de ingresos:", e);
    }

    // Gráfico distribución por plan (gráfico de pastel)
    try {
      crearGraficoSeguro('graficoPlan', 'pie', {
        type: 'doughnut',
        data: {
          labels: planesNombres,
          datasets: [{
            label: 'Usuarios por plan',
            data: datosPlanes,
            backgroundColor: COLORES.planes,
            borderColor: 'white',
            borderWidth: 2,
            hoverOffset: 15
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: '50%',
          plugins: {
            legend: {
              position: 'right',
              labels: {
                boxWidth: 12,
                font: {
                  size: 11
                }
              }
            },
            tooltip: {
              callbacks: {
                label: function(context) {
                  const value = context.parsed;
                  const index = context.dataIndex;
                  const total = context.dataset.data.reduce((acc, val) => acc + val, 0);
                  const percentage = Math.round((value / total) * 100);
                  const potentialIncome = ingresosPotencialesPlanes[index];
                  
                  return [
                    `${context.label}: ${value} usuarios (${percentage}%)`,
                    `Ingreso potencial: ${formatoCOP(potentialIncome)}`
                  ];
                }
              }
            },
            datalabels: {
              color: 'white',
              font: {
                weight: 'bold'
              },
              formatter: function(value, context) {
                if (value === 0) return '';
                const total = context.dataset.data.reduce((acc, val) => acc + val, 0);
                const percentage = Math.round((value / total) * 100);
                return percentage + '%';
              }
            }
          }
        }
      });
    } catch (e) {
      console.error("Error en gráfico de planes:", e);
    }

    // Gráfico de productos más vendidos (gráfico de barras horizontales)
    try {
      crearGraficoSeguro('graficoProductos', 'bar', {
        type: 'bar',
        data: {
          labels: productosNombres,
          datasets: [{
            label: 'Unidades Vendidas',
            data: productosCantidades,
            backgroundColor: COLORES.productos.bg,
            borderColor: COLORES.productos.border,
            borderWidth: 1,
            borderRadius: 4
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          indexAxis: 'y',
          plugins: {
            legend: {
              display: false
            },
            tooltip: {
              callbacks: {
                label: function(context) {
                  return `${context.dataset.label}: ${context.parsed.x} unidades`;
                }
              }
            },
            datalabels: {
              align: 'end',
              anchor: 'end',
              color: COLORES.productos.border,
              font: {
                weight: 'bold'
              },
              formatter: function(value) {
                return value + ' uds.';
              }
            }
          },
          scales: {
            x: {
              beginAtZero: true,
              grid: {
                display: false
              }
            },
            y: {
              grid: {
                display: false
              }
            }
          }
        }
      });
    } catch (e) {
      console.error("Error en gráfico de productos vendidos:", e);
    }

    // Gráfico de ingresos por producto (barras apiladas con margen)
    try {
      // Calcular costos para productos
      const productosCostos = productosIngresos.map(ingreso => ingreso * 0.6);
      
      crearGraficoSeguro('graficoIngresosProductos', 'bar', {
        type: 'bar',
        data: {
          labels: productosNombres,
          datasets: [
            {
              label: 'Margen',
              data: productosMargenes,
              backgroundColor: COLORES.margenes.border,
              stack: 'Stack 0'
            },
            {
              label: 'Costo',
              data: productosCostos,
              backgroundColor: '#e5e7eb',
              stack: 'Stack 0'
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          indexAxis: 'y',
          plugins: {
            legend: {
              position: 'top',
              labels: {
                boxWidth: 12,
                usePointStyle: true
              }
            },
            tooltip: {
              callbacks: {
                label: function(context) {
                  const datasetLabel = context.dataset.label;
                  const value = context.parsed.x;
                  return `${datasetLabel}: ${formatoCOP(value)}`;
                },
                footer: function(tooltipItems) {
                  const index = tooltipItems[0].dataIndex;
                  return `Total: ${formatoCOP(productosIngresos[index])}`;
                }
              }
            },
            datalabels: {
              display: function(context) {
                return context.datasetIndex === 0; // Solo mostrar para el margen
              },
              color: 'white',
              font: {
                weight: 'bold',
                size: 10
              },
              formatter: function(value, context) {
                if (value === 0) return '';
                const index = context.dataIndex;
                const total = productosIngresos[index];
                if (total === 0) return '';
                const percentage = Math.round((value / total) * 100);
                return percentage + '%';
              }
            }
          },
          scales: {
            x: {
              stacked: true,
              beginAtZero: true,
              grid: {
                display: false
              },
              ticks: {
                callback: function(value) {
                  return formatoCOP(value);
                }
              }
            },
            y: {
              stacked: true,
              grid: {
                display: false
              }
            }
          }
        }
      });
    } catch (e) {
      console.error("Error en gráfico de ingresos por producto:", e);
    }

    console.log('Gráficos financieros inicializados correctamente');
  } catch (error) {
    console.error("Error al inicializar gráficos:", error);
    mostrarErrorGraficos();
  }
}

// Inicializar la carga de scripts y gráficos
function inicializarFinanzasCharts() {
  // Verificar si Chart.js ya está cargado
  if (typeof Chart === 'undefined') {
    console.log('Chart.js no detectado, cargando desde archivos locales...');
    
    // Primero cargar Chart.js desde archivo local
    loadScript(
      '/static/js/vendor/chart.min.js',
      null,
      () => {
        // Después cargar el plugin de datalabels desde archivo local
        loadScript(
          '/static/js/vendor/chartjs-plugin-datalabels.min.js',
          null,
          inicializarGraficos
        );
      }
    );
  } else {
    // Chart.js ya está disponible
    console.log('Chart.js ya está disponible en la página');
    // Comprobar si el plugin datalabels está disponible
    if (typeof ChartDataLabels === 'undefined') {
      loadScript(
        '/static/js/vendor/chartjs-plugin-datalabels.min.js',
        null,
        () => setTimeout(inicializarGraficos, 100)
      );
    } else {
      setTimeout(inicializarGraficos, 100);
    }
  }
}

// Ejecutar cuando el DOM esté cargado
document.addEventListener('DOMContentLoaded', inicializarFinanzasCharts); 