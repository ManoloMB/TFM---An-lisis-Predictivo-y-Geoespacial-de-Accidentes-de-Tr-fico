from fastapi import FastAPI
from pydantic import BaseModel
import pickle
import pandas as pd
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import Optional
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Definir esquema de entrada con Pydantic
class InputData(BaseModel):
    tipo_vehiculo: str
    tipo_persona: str
    tipo_accidente: str
    sexo: str
    rango_edad: str
    estado_meteorológico: str
    cod_distrito: Optional[int] = None
    coordenada_x_utm: Optional[float] = None
    coordenada_y_utm: Optional[float] = None

app = FastAPI(title="API Predicción Lesividad", description="API para predecir lesividad en accidentes de tráfico")

# Cargar modelos al inicio de la aplicación
try:
    # Cargar modelo, preprocesador y label encoder al inicio (distrito)
    with open('modelos/xgboost_binario_balanceado_smote_modelo_distrito.pkl', 'rb') as f:
        model_distrito = pickle.load(f)

    with open('modelos/preprocessor/xgboost_binario_balanceado_smote_preprocessor_distrito.pkl', 'rb') as f:
        preprocessor_distrito = pickle.load(f)

    with open('modelos/label_encoder/xgboost_binario_balanceado_smote_label_encoder_distrito.pkl', 'rb') as f:
        label_encoder_distrito = pickle.load(f)

    # Cargar modelo, preprocesador y label encoder al inicio (coordenadas)
    with open('modelos/xgboost_binario_balanceado_smote_modelo_coordenadas.pkl', 'rb') as f:
        model_coordenadas = pickle.load(f)

    with open('modelos/preprocessor/xgboost_binario_balanceado_smote_preprocessor_coordenadas.pkl', 'rb') as f:
        preprocessor_coordenadas = pickle.load(f)

    with open('modelos/label_encoder/xgboost_binario_balanceado_smote_label_encoder_coordenadas.pkl', 'rb') as f:
        label_encoder_coordenadas = pickle.load(f)

    logger.info("Modelos cargados correctamente.")

except FileNotFoundError as e:
    logger.error(f"Archivo de modelo no encontrado: {e}")
    raise HTTPException(status_code=500, detail="Modelos no encontrados")
except Exception as e:
    logger.error(f"Error cargando modelos: {e}")
    raise HTTPException(status_code=500, detail="Error al cargar modelos")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Maneja errores de validación de entrada"""
    logger.warning(f"Error de validación: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body}
    )

@app.get("/")
async def root():
    """Endpoint de bienvenida"""
    return {
        "mensaje": "API Predicción Lesividad en Accidentes",
        "status": "activo",
        "endpoints": ["/predict", "/docs"]
    }

@app.get("/health")
async def health_check():
    """Endpoint para verificar el estado de la API"""
    return {"status": "healthy", "modelos": "cargados"}

@app.post("/predict")
async def predict(data: InputData):
    """
    Predice la lesividad de un accidente basándose en las características proporcionadas.
    
    Args:
        data: Datos del accidente (InputData)
    
    Returns:
        Dict con prediction (0/1) y probability (float)
    """
    try:
        logger.info(f"Recibida solicitud de predicción")
        
        # Validar datos de entrada
        if data.cod_distrito is None and (data.coordenada_x_utm is None or data.coordenada_y_utm is None):
            logger.warning("Datos de ubicación insuficientes")
            raise HTTPException(
                status_code=400, 
                detail="Debe proporcionar 'cod_distrito' o ambas coordenadas UTM (coordenada_x_utm y coordenada_y_utm)"
            )
        
        # Determinar qué modelo usar
        if data.cod_distrito is not None:
            # Usar modelo con distrito
            preprocessor = preprocessor_distrito
            model = model_distrito
            label_encoder = label_encoder_distrito
            logger.info("Usando modelo con distrito")
        elif data.coordenada_x_utm is not None and data.coordenada_y_utm is not None:
            # Usar modelo con coordenadas
            preprocessor = preprocessor_coordenadas
            model = model_coordenadas
            label_encoder = label_encoder_coordenadas
            logger.info("Usando modelo con coordenadas")
        else:
            logger.error("Lógica de selección de modelo falló")
            raise HTTPException(
                status_code=400,
                detail="Error interno: no se pudo determinar qué modelo usar"
            )
        
        # Crear DataFrame y preprocesar
        data_dict = data.model_dump()
        df = pd.DataFrame([data_dict])
        
        logger.info(f"Datos procesados: {len(df)} filas, {len(df.columns)} columnas")
        
        # Preprocesar datos
        X_prep = preprocessor.transform(df)
        
        # Realizar predicción
        probas = model.predict_proba(X_prep)
        pred_class_encoded = probas.argmax(axis=1)
        y_pred = label_encoder.inverse_transform(pred_class_encoded)
        pred_prob = probas[0, pred_class_encoded[0]]
        
        resultado = {
            "prediction": int(y_pred[0]),
            "probability": float(pred_prob)
        }
        
        logger.info(f"Predicción exitosa: {resultado}")
        return resultado
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error inesperado en predicción: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Error interno del servidor durante la predicción"
        )

@app.get("/modelo/info")
async def modelo_info():
    """Información sobre los modelos cargados"""
    try:
        return {
            "modelos_disponibles": ["distrito", "coordenadas"],
            "variables_entrada": [
                "tipo_vehiculo", "tipo_persona", "tipo_accidente", 
                "sexo", "rango_edad", "estado_meteorológico"
            ],
            "ubicacion_opciones": ["cod_distrito", "coordenada_x_utm + coordenada_y_utm"],
            "salida": {
                "prediction": "0 = Con asistencia, 1 = Sin asistencia",
                "probability": "Probabilidad de la clase predicha (0.0-1.0)"
            }
        }
    except Exception as e:
        logger.error(f"Error obteniendo info del modelo: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo información")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)