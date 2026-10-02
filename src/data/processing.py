def converter_moeda_brasileira(valor):
    
    if valor is None:
        return None
    
    valor = str(valor).strip()
    
    if valor == "":
        return None
    
    valor = valor.replace(".", "")
    valor = valor.replace(",", ".")
    
    return float(valor)