#!/bin/bash

# Colores para la terminal
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=======================================================${NC}"
echo -e "${BLUE}GENERADOR DE EJECUTABLES MULTISISTEMA - GIMNASIO DB${NC}"
echo -e "${BLUE}=======================================================${NC}"
echo ""
echo "Este script generará ejecutables para diferentes sistemas operativos."
echo ""
echo "Opciones:"
echo "1. Generar ejecutable para Windows"
echo "2. Generar ejecutable para Linux"
echo "3. Generar ejecutable para macOS"
echo "4. Generar ejecutables para todos los sistemas"
echo "5. Incluir base de datos en los ejecutables"
echo "6. Salir"
echo ""

incluir_db=""

while true; do
    read -p "Seleccione una opción (1-6): " opcion
    
    case $opcion in
        1)
            echo ""
            echo -e "${YELLOW}Generando ejecutable para Windows...${NC}"
            python empaquetar_app.py --windows $incluir_db
            break
            ;;
        2)
            echo ""
            echo -e "${YELLOW}Generando ejecutable para Linux...${NC}"
            python empaquetar_app.py --linux $incluir_db
            break
            ;;
        3)
            echo ""
            echo -e "${YELLOW}Generando ejecutable para macOS...${NC}"
            python empaquetar_app.py --macos $incluir_db
            break
            ;;
        4)
            echo ""
            echo -e "${YELLOW}Generando ejecutables para todos los sistemas...${NC}"
            python empaquetar_app.py --all $incluir_db
            break
            ;;
        5)
            incluir_db="--include-db"
            echo ""
            echo -e "${GREEN}Se incluirá la base de datos en los ejecutables.${NC}"
            ;;
        6)
            echo ""
            echo "Saliendo..."
            exit 0
            ;;
        *)
            echo ""
            echo -e "${RED}Opción inválida. Por favor, seleccione una opción válida.${NC}"
            ;;
    esac
done

echo ""
echo -e "${GREEN}===============================================${NC}"
echo -e "${GREEN}Proceso de generación de ejecutables completado${NC}"
echo -e "${GREEN}===============================================${NC}"
echo ""
echo "Los ejecutables se encuentran en la carpeta 'dist/'"
echo ""
read -p "Presione ENTER para continuar..." 