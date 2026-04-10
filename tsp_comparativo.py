import random
from sklearn.cluster import KMeans


def calcular_distancia_total(ruta, matriz_distancias, indices, cerrar_ciclo=False):
    total = 0.0

    for i in range(len(ruta) - 1):
        idx_a = indices[id(ruta[i])]
        idx_b = indices[id(ruta[i + 1])]
        total += matriz_distancias[idx_a][idx_b]

    if cerrar_ciclo and len(ruta) > 1:
        idx_inicio = indices[id(ruta[0])]
        idx_final = indices[id(ruta[-1])]
        total += matriz_distancias[idx_final][idx_inicio]

    return round(total, 2)


def calcular_duracion_total_min(ruta, matriz_duraciones, indices, cerrar_ciclo=False):
    total = 0.0

    for i in range(len(ruta) - 1):
        idx_a = indices[id(ruta[i])]
        idx_b = indices[id(ruta[i + 1])]
        total += matriz_duraciones[idx_a][idx_b]

    if cerrar_ciclo and len(ruta) > 1:
        idx_inicio = indices[id(ruta[0])]
        idx_final = indices[id(ruta[-1])]
        total += matriz_duraciones[idx_final][idx_inicio]

    return round(total, 2)


def calcular_costo_gasolina(distancia_km, precio_gasolina, rendimiento_km_litro):
    if rendimiento_km_litro <= 0:
        return 0
    litros_consumidos = distancia_km / rendimiento_km_litro
    return round(litros_consumidos * precio_gasolina, 2)


def calcular_costo_mano_obra(tiempo_horas, salario_hora):
    return round(tiempo_horas * salario_hora, 2)


def calcular_costos(
    distancia_km,
    tiempo_desplazamiento_min,
    precio_gasolina,
    rendimiento_km_litro,
    salario_hora,
    num_clientes=0,
    tiempo_servicio_minutos=5
):
    tiempo_servicio_min_total = num_clientes * tiempo_servicio_minutos
    tiempo_total_min = tiempo_desplazamiento_min + tiempo_servicio_min_total

    tiempo_desplazamiento_horas = round(tiempo_desplazamiento_min / 60.0, 2)
    tiempo_servicio_horas = round(tiempo_servicio_min_total / 60.0, 2)
    tiempo_total_horas = round(tiempo_total_min / 60.0, 2)

    costo_gasolina = calcular_costo_gasolina(
        distancia_km,
        precio_gasolina,
        rendimiento_km_litro
    )
    costo_mano_obra = calcular_costo_mano_obra(tiempo_total_horas, salario_hora)
    costo_total = round(costo_gasolina + costo_mano_obra, 2)

    return {
        "tiempo_desplazamiento_min": round(tiempo_desplazamiento_min, 2),
        "tiempo_servicio_min": round(tiempo_servicio_min_total, 2),
        "tiempo_total_min": round(tiempo_total_min, 2),
        "tiempo_desplazamiento_horas": tiempo_desplazamiento_horas,
        "tiempo_servicio_horas": tiempo_servicio_horas,
        "tiempo_horas": tiempo_total_horas,
        "costo_gasolina": round(costo_gasolina, 2),
        "costo_mano_obra": round(costo_mano_obra, 2),
        "costo_total": round(costo_total, 2)
    }


def construir_detalle_ruta(
    ruta,
    matriz_distancias,
    matriz_duraciones,
    indices,
    tiempo_servicio_minutos=5
):
    detalle = []
    tiempo_acumulado = 0.0

    for i, punto in enumerate(ruta):
        if i == 0:
            detalle.append({
                "orden": 0,
                "nombre": punto["nombre"],
                "tipo": "origen",
                "distancia_desde_anterior_km": 0.0,
                "tiempo_viaje_min": 0.0,
                "tiempo_servicio_min": 0.0,
                "tiempo_llegada_min": 0.0,
                "tiempo_salida_min": 0.0,
                "tiempo_acumulado_min": 0.0
            })
            continue

        anterior = ruta[i - 1]
        idx_a = indices[id(anterior)]
        idx_b = indices[id(punto)]

        distancia_tramo = matriz_distancias[idx_a][idx_b]
        tiempo_viaje = matriz_duraciones[idx_a][idx_b]

        tiempo_llegada = tiempo_acumulado + tiempo_viaje
        tiempo_salida = tiempo_llegada + tiempo_servicio_minutos
        tiempo_acumulado = tiempo_salida

        detalle.append({
            "orden": i,
            "nombre": punto["nombre"],
            "tipo": "cliente",
            "distancia_desde_anterior_km": round(distancia_tramo, 2),
            "tiempo_viaje_min": round(tiempo_viaje, 2),
            "tiempo_servicio_min": round(tiempo_servicio_minutos, 2),
            "tiempo_llegada_min": round(tiempo_llegada, 2),
            "tiempo_salida_min": round(tiempo_salida, 2),
            "tiempo_acumulado_min": round(tiempo_acumulado, 2)
        })

    return detalle


def agrupar_con_kmeans(destinos, num_clusters):
    coordenadas = [[p["lat"], p["lon"]] for p in destinos]

    modelo = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
    etiquetas = modelo.fit_predict(coordenadas)

    clusters = {}
    for i, etiqueta in enumerate(etiquetas):
        clusters.setdefault(int(etiqueta), []).append(destinos[i])

    return clusters


def vecino_mas_cercano(origen, destinos, matriz_distancias, indices):
    if not destinos:
        return [origen]

    no_visitados = destinos[:]
    ruta = [origen]
    actual = origen

    while no_visitados:
        idx_actual = indices[id(actual)]
        siguiente = min(
            no_visitados,
            key=lambda p: matriz_distancias[idx_actual][indices[id(p)]]
        )
        ruta.append(siguiente)
        no_visitados.remove(siguiente)
        actual = siguiente

    return ruta


def aco_ruta(
    origen,
    destinos,
    matriz_distancias,
    indices,
    num_hormigas=20,
    num_iteraciones=60,
    alpha=1,
    beta=3,
    evaporacion=0.5
):
    if not destinos:
        return [origen]

    if len(destinos) == 1:
        return [origen] + destinos

    n = len(destinos) + 1
    feromonas = [[1.0 for _ in range(n)] for _ in range(n)]

    mejor_ruta = None
    mejor_distancia = float("inf")

    for _ in range(num_iteraciones):
        rutas_hormigas = []

        for _ in range(num_hormigas):
            no_visitados = destinos[:]
            ruta = [origen]
            actual = origen

            while no_visitados:
                idx_actual = indices[id(actual)]

                probabilidades = []
                suma = 0.0

                for p in no_visitados:
                    idx_p = indices[id(p)]
                    distancia = matriz_distancias[idx_actual][idx_p]

                    if distancia <= 0:
                        distancia = 0.0001

                    tau = feromonas[idx_actual][idx_p] ** alpha
                    eta = (1.0 / distancia) ** beta
                    valor = tau * eta
                    probabilidades.append((p, valor))
                    suma += valor

                if suma == 0:
                    siguiente = random.choice(no_visitados)
                else:
                    r = random.random()
                    acumulado = 0.0
                    siguiente = no_visitados[0]

                    for p, prob in probabilidades:
                        acumulado += prob / suma
                        if r <= acumulado:
                            siguiente = p
                            break

                ruta.append(siguiente)
                no_visitados.remove(siguiente)
                actual = siguiente

            distancia_ruta = calcular_distancia_total(ruta, matriz_distancias, indices)
            rutas_hormigas.append((ruta, distancia_ruta))

            if distancia_ruta < mejor_distancia:
                mejor_distancia = distancia_ruta
                mejor_ruta = ruta[:]

        for i in range(n):
            for j in range(n):
                feromonas[i][j] *= (1 - evaporacion)
                if feromonas[i][j] < 0.0001:
                    feromonas[i][j] = 0.0001

        for ruta, distancia in rutas_hormigas:
            if distancia <= 0:
                continue
            aporte = 1.0 / distancia

            for i in range(len(ruta) - 1):
                a = indices[id(ruta[i])]
                b = indices[id(ruta[i + 1])]
                feromonas[a][b] += aporte
                feromonas[b][a] += aporte

    return mejor_ruta if mejor_ruta else [origen] + destinos


def crear_individuo(destinos):
    individuo = destinos.copy()
    random.shuffle(individuo)
    return individuo


def crear_poblacion(destinos, tam_poblacion):
    return [crear_individuo(destinos) for _ in range(tam_poblacion)]


def fitness(individuo, origen, matriz_distancias, indices):
    ruta = [origen] + individuo
    distancia = calcular_distancia_total(
        ruta,
        matriz_distancias,
        indices,
        cerrar_ciclo=False
    )
    if distancia == 0:
        return float("inf")
    return 1.0 / distancia


def seleccion_torneo(poblacion, origen, matriz_distancias, indices, k=3):
    participantes = random.sample(poblacion, min(k, len(poblacion)))
    participantes.sort(
        key=lambda ind: fitness(ind, origen, matriz_distancias, indices),
        reverse=True
    )
    return participantes[0][:]


def crossover_ordenado(padre1, padre2):
    n = len(padre1)

    if n <= 1:
        return padre1[:]

    inicio = random.randint(0, n - 2)
    fin = random.randint(inicio + 1, n - 1)

    hijo = [None] * n
    hijo[inicio:fin + 1] = padre1[inicio:fin + 1]

    elementos_restantes = [gen for gen in padre2 if gen not in hijo]

    idx_restante = 0
    for i in range(n):
        if hijo[i] is None:
            hijo[i] = elementos_restantes[idx_restante]
            idx_restante += 1

    return hijo


def mutacion_swap(individuo, prob_mutacion=0.1):
    mutado = individuo[:]

    if len(mutado) < 2:
        return mutado

    if random.random() < prob_mutacion:
        i, j = random.sample(range(len(mutado)), 2)
        mutado[i], mutado[j] = mutado[j], mutado[i]

    return mutado


def algoritmo_genetico_ruta(
    origen,
    destinos,
    matriz_distancias,
    indices,
    tam_poblacion=60,
    num_generaciones=120,
    prob_mutacion=0.15,
    elitismo=0.2
):
    if not destinos:
        return [origen]

    if len(destinos) == 1:
        return [origen] + destinos

    poblacion = crear_poblacion(destinos, tam_poblacion)

    mejor_individuo = None
    mejor_distancia = float("inf")

    for _ in range(num_generaciones):
        poblacion_ordenada = sorted(
            poblacion,
            key=lambda ind: calcular_distancia_total(
                [origen] + ind,
                matriz_distancias,
                indices,
                cerrar_ciclo=False
            )
        )

        mejor_actual = poblacion_ordenada[0]
        distancia_actual = calcular_distancia_total(
            [origen] + mejor_actual,
            matriz_distancias,
            indices,
            cerrar_ciclo=False
        )

        if distancia_actual < mejor_distancia:
            mejor_distancia = distancia_actual
            mejor_individuo = mejor_actual[:]

        num_elite = max(1, int(tam_poblacion * elitismo))
        nueva_poblacion = [ind[:] for ind in poblacion_ordenada[:num_elite]]

        while len(nueva_poblacion) < tam_poblacion:
            padre1 = seleccion_torneo(poblacion, origen, matriz_distancias, indices)
            padre2 = seleccion_torneo(poblacion, origen, matriz_distancias, indices)

            hijo = crossover_ordenado(padre1, padre2)
            hijo = mutacion_swap(hijo, prob_mutacion)

            nueva_poblacion.append(hijo)

        poblacion = nueva_poblacion

    return [origen] + mejor_individuo


def procesar_rutas_con_kmeans(
    origen,
    destinos,
    num_clusters,
    funcion_matriz,
    precio_gasolina=16000,
    rendimiento_km_litro=40,
    salario_hora=7000,
    tiempo_servicio_minutos=5
):
    clusters = agrupar_con_kmeans(destinos, num_clusters)

    total_vecino = 0.0
    total_aco = 0.0
    total_genetico = 0.0

    total_duracion_vecino = 0.0
    total_duracion_aco = 0.0
    total_duracion_gen = 0.0

    resultados_clusters = []

    for cluster_id, puntos_cluster in clusters.items():
        puntos = [origen] + puntos_cluster
        matrices = funcion_matriz(puntos)

        if not matrices:
            return {"error": "Error calculando matriz OSRM"}

        matriz_distancias = matrices["distancias_km"]
        matriz_duraciones = matrices["duraciones_min"]

        indices = {id(p): i for i, p in enumerate(puntos)}

        ruta_vecino = vecino_mas_cercano(origen, puntos_cluster, matriz_distancias, indices)
        dist_vecino = calcular_distancia_total(ruta_vecino, matriz_distancias, indices)
        dur_vecino = calcular_duracion_total_min(ruta_vecino, matriz_duraciones, indices)
        total_vecino += dist_vecino
        total_duracion_vecino += dur_vecino

        ruta_aco = aco_ruta(origen, puntos_cluster, matriz_distancias, indices)
        dist_aco = calcular_distancia_total(ruta_aco, matriz_distancias, indices)
        dur_aco = calcular_duracion_total_min(ruta_aco, matriz_duraciones, indices)
        total_aco += dist_aco
        total_duracion_aco += dur_aco

        ruta_gen = algoritmo_genetico_ruta(origen, puntos_cluster, matriz_distancias, indices)
        dist_gen = calcular_distancia_total(ruta_gen, matriz_distancias, indices)
        dur_gen = calcular_duracion_total_min(ruta_gen, matriz_duraciones, indices)
        total_genetico += dist_gen
        total_duracion_gen += dur_gen

        detalle_clientes = construir_detalle_ruta(
            ruta=ruta_gen,
            matriz_distancias=matriz_distancias,
            matriz_duraciones=matriz_duraciones,
            indices=indices,
            tiempo_servicio_minutos=tiempo_servicio_minutos
        )

        costos_cluster = calcular_costos(
            distancia_km=dist_gen,
            tiempo_desplazamiento_min=dur_gen,
            precio_gasolina=precio_gasolina,
            rendimiento_km_litro=rendimiento_km_litro,
            salario_hora=salario_hora,
            num_clientes=len(puntos_cluster),
            tiempo_servicio_minutos=tiempo_servicio_minutos
        )

        resultados_clusters.append({
            "cluster": cluster_id + 1,
            "distancia_km": round(dist_gen, 2),
            "tiempo_desplazamiento_min": costos_cluster["tiempo_desplazamiento_min"],
            "tiempo_servicio_min": costos_cluster["tiempo_servicio_min"],
            "tiempo_total_min": costos_cluster["tiempo_total_min"],
            "tiempo_desplazamiento_horas": costos_cluster["tiempo_desplazamiento_horas"],
            "tiempo_servicio_horas": costos_cluster["tiempo_servicio_horas"],
            "tiempo_horas": costos_cluster["tiempo_horas"],
            "costo_gasolina": costos_cluster["costo_gasolina"],
            "costo_mano_obra": costos_cluster["costo_mano_obra"],
            "costo_total": costos_cluster["costo_total"],
            "ruta_nombres": [p["nombre"] for p in ruta_gen],
            "ruta_coordenadas": [
                {
                    "nombre": p["nombre"],
                    "lat": p["lat"],
                    "lon": p["lon"]
                }
                for p in ruta_gen
            ],
            "detalle_clientes": detalle_clientes
        })

    costos_vecino = calcular_costos(
        distancia_km=round(total_vecino, 2),
        tiempo_desplazamiento_min=round(total_duracion_vecino, 2),
        precio_gasolina=precio_gasolina,
        rendimiento_km_litro=rendimiento_km_litro,
        salario_hora=salario_hora,
        num_clientes=len(destinos),
        tiempo_servicio_minutos=tiempo_servicio_minutos
    )

    costos_aco = calcular_costos(
        distancia_km=round(total_aco, 2),
        tiempo_desplazamiento_min=round(total_duracion_aco, 2),
        precio_gasolina=precio_gasolina,
        rendimiento_km_litro=rendimiento_km_litro,
        salario_hora=salario_hora,
        num_clientes=len(destinos),
        tiempo_servicio_minutos=tiempo_servicio_minutos
    )

    costos_gen = calcular_costos(
        distancia_km=round(total_genetico, 2),
        tiempo_desplazamiento_min=round(total_duracion_gen, 2),
        precio_gasolina=precio_gasolina,
        rendimiento_km_litro=rendimiento_km_litro,
        salario_hora=salario_hora,
        num_clientes=len(destinos),
        tiempo_servicio_minutos=tiempo_servicio_minutos
    )

    comparativa = [
        {
            "algoritmo": "K-Means + Vecino",
            "distancia_km": round(total_vecino, 2),
            "tiempo_desplazamiento_min": costos_vecino["tiempo_desplazamiento_min"],
            "tiempo_servicio_min": costos_vecino["tiempo_servicio_min"],
            "tiempo_total_min": costos_vecino["tiempo_total_min"],
            "tiempo_desplazamiento_horas": costos_vecino["tiempo_desplazamiento_horas"],
            "tiempo_servicio_horas": costos_vecino["tiempo_servicio_horas"],
            "tiempo_horas": costos_vecino["tiempo_horas"],
            "costo_gasolina": costos_vecino["costo_gasolina"],
            "costo_mano_obra": costos_vecino["costo_mano_obra"],
            "costo_total": costos_vecino["costo_total"]
        },
        {
            "algoritmo": "K-Means + ACO",
            "distancia_km": round(total_aco, 2),
            "tiempo_desplazamiento_min": costos_aco["tiempo_desplazamiento_min"],
            "tiempo_servicio_min": costos_aco["tiempo_servicio_min"],
            "tiempo_total_min": costos_aco["tiempo_total_min"],
            "tiempo_desplazamiento_horas": costos_aco["tiempo_desplazamiento_horas"],
            "tiempo_servicio_horas": costos_aco["tiempo_servicio_horas"],
            "tiempo_horas": costos_aco["tiempo_horas"],
            "costo_gasolina": costos_aco["costo_gasolina"],
            "costo_mano_obra": costos_aco["costo_mano_obra"],
            "costo_total": costos_aco["costo_total"]
        },
        {
            "algoritmo": "K-Means + Genético",
            "distancia_km": round(total_genetico, 2),
            "tiempo_desplazamiento_min": costos_gen["tiempo_desplazamiento_min"],
            "tiempo_servicio_min": costos_gen["tiempo_servicio_min"],
            "tiempo_total_min": costos_gen["tiempo_total_min"],
            "tiempo_desplazamiento_horas": costos_gen["tiempo_desplazamiento_horas"],
            "tiempo_servicio_horas": costos_gen["tiempo_servicio_horas"],
            "tiempo_horas": costos_gen["tiempo_horas"],
            "costo_gasolina": costos_gen["costo_gasolina"],
            "costo_mano_obra": costos_gen["costo_mano_obra"],
            "costo_total": costos_gen["costo_total"]
        }
    ]

    mejor = min(comparativa, key=lambda x: x["costo_total"])

    return {
        "metodo_principal": "K-Means",
        "algoritmo_secundario": "Comparativo",
        "mejor_algoritmo": mejor["algoritmo"],
        "distancia_total_km": mejor["distancia_km"],
        "tiempo_desplazamiento_min": mejor["tiempo_desplazamiento_min"],
        "tiempo_servicio_min": mejor["tiempo_servicio_min"],
        "tiempo_total_min": mejor["tiempo_total_min"],
        "tiempo_desplazamiento_horas": mejor["tiempo_desplazamiento_horas"],
        "tiempo_servicio_horas": mejor["tiempo_servicio_horas"],
        "tiempo_total_horas": mejor["tiempo_horas"],
        "costo_total": mejor["costo_total"],
        "num_clusters": num_clusters,
        "parametros_costos": {
            "precio_gasolina": precio_gasolina,
            "rendimiento_km_litro": rendimiento_km_litro,
            "salario_hora": salario_hora,
            "tiempo_servicio_minutos": tiempo_servicio_minutos
        },
        "clusters": resultados_clusters,
        "comparativa": comparativa
    }