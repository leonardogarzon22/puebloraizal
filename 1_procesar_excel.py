import pandas as pd
import json
import os

# Nombre exacto de tu archivo principal
ARCHIVO_EXCEL = 'conpes_dc_38_plan_accion_pp_raizal.xlsx'
ARCHIVO_SALIDA = 'contexto_conpes_38.json'

def extraer_informacion_hoja(df, nombre_hoja):
    """
    Busca los datos clave dentro de la hoja de Excel.
    """
    datos_extraidos = {
        "id_ficha": nombre_hoja,
        "nombre_indicador": "No especificado",
        "entidad_responsable": "No especificada",
        "descripcion": "No especificada",
        "relacion_resultado": "No especificada"
    }
    
    # Llenamos los espacios vacíos del Excel para evitar errores
    df = df.fillna('')
    
    for index, fila in df.iterrows():
        # Tomamos solo las celdas que tengan texto
        valores = [str(val).strip() for val in fila.values if str(val).strip() != '']
        if not valores:
            continue
            
        columna_clave = valores[0].lower()
        
        # Extracción lógica basada en palabras clave
        if 'nombre del indicador' in columna_clave:
            if len(valores) > 1: 
                datos_extraidos["nombre_indicador"] = valores[1]
                
        elif 'entidad' in columna_clave and 'responsable' not in columna_clave:
             # A veces dice "Entidad" y la celda de al lado tiene el nombre
             if len(valores) > 1:
                 datos_extraidos["entidad_responsable"] = valores[1]
                 
        elif 'descripción del indicador' in columna_clave or 'descripción del producto' in columna_clave:
            if len(valores) > 1:
                datos_extraidos["descripcion"] = valores[1]
                
        elif 'relación entre el indicador' in columna_clave:
            if len(valores) > 1:
                datos_extraidos["relacion_resultado"] = valores[1]

    return datos_extraidos

def main():
    if not os.path.exists(ARCHIVO_EXCEL):
        print(f"Error: No se encontró el archivo '{ARCHIVO_EXCEL}' en la carpeta actual.")
        return

    print(f"Leyendo el archivo Excel: {ARCHIVO_EXCEL} (esto puede tomar unos segundos)...")
    try:
        # sheet_name=None le dice a Pandas que lea TODAS las hojas del Excel
        hojas_excel = pd.read_excel(ARCHIVO_EXCEL, sheet_name=None, engine='openpyxl')
        consolidado = []
        
        for nombre_hoja, dataframe in hojas_excel.items():
            # Filtramos para analizar solo las hojas que son fichas (empiezan por "Ficha")
            if 'ficha' in nombre_hoja.lower() or 'p ' in nombre_hoja.lower() or 'r_' in nombre_hoja.lower():
                info = extraer_informacion_hoja(dataframe, nombre_hoja)
                consolidado.append(info)
                print(f"✔ Procesada: {nombre_hoja}")
                
        # Guardamos todo en un solo JSON
        with open(ARCHIVO_SALIDA, 'w', encoding='utf-8') as f:
            json.dump(consolidado, f, ensure_ascii=False, indent=4)
            
        print(f"\n¡Éxito! Se consolidó la información de {len(consolidado)} fichas en el archivo '{ARCHIVO_SALIDA}'.")
        
    except Exception as e:
        print(f"Ocurrió un error procesando el Excel: {e}")

if __name__ == '__main__':
    main()