import numpy as np
import os
import time

from Problem.SCP.problem import SCP
from Metaheuristics.imports import iterarPSO, iterarFOX, iterarWOA, iterarGWO
from Diversity.imports import diversidadHussain,porcentajesXLPXPT
from Discretization import discretization as b
from util import util
from BD.sqlite import BD

def solverSCP(id, mh, maxIter, pop, instances, DS, repairType, param):
    
    dirResult = './Resultados/'
    instance = SCP(instances)
    
    chaotic_map = None
    
    # tomo el tiempo inicial de la ejecucion
    initialTime = time.time()
    
    initializationTime1 = time.time()

    print("------------------------------------------------------------------------------------------------------")
    print("instancia SCP a resolver: "+instances)
    
    results = open(dirResult+mh+"_"+instances.split(".")[0]+"_"+str(id)+".csv", "w")
    results.write(
        f'iter,fitness,time,XPL,XPT,DIV\n'
    )
    
    # Genero una población inicial binaria, esto ya que nuestro problema es binario
    population = np.random.randint(low=0, high=2, size = (pop, instance.getColumns()))

    maxDiversity = diversidadHussain(population)
    XPL , XPT, state = porcentajesXLPXPT(maxDiversity, maxDiversity)
    
    # Genero un vector donde almacenaré los fitness de cada individuo
    fitness = np.zeros(pop)

    # Genero un vetor dedonde tendré mis soluciones rankeadas
    solutionsRanking = np.zeros(pop)
    
    # calculo de factibilidad de cada individuo y calculo del fitness inicial
    for i in range(population.__len__()):
        flag, aux = instance.factibilityTest(population[i])
        if not flag: #solucion infactible
            population[i] = instance.repair(population[i], repairType)
            

        fitness[i] = instance.fitness(population[i])
        
    solutionsRanking = np.argsort(fitness) # rankings de los mejores fitnes
    bestRowAux = solutionsRanking[0]
    # DETERMINO MI MEJOR SOLUCION Y LA GUARDO 
    best = population[bestRowAux].copy()
    bestFitness = fitness[bestRowAux]
    
    matrixBin = population.copy()
    
    initializationTime2 = time.time()
    
    # mostramos nuestro fitness iniciales
    print("------------------------------------------------------------------------------------------------------")
    print("fitness incial: "+str(fitness))
    print("best fitness inicial: "+str(bestFitness))
    print("------------------------------------------------------------------------------------------------------")
    if mh == "GA":
        print("COMIENZA A TRABAJAR LA METAHEURISTICA "+mh+ " / Reparacion: "+repairType)
    else: 
        print("COMIENZA A TRABAJAR LA METAHEURISTICA "+mh+ " / Binarizacion: "+ str(DS) + " / Reparacion: "+repairType)
    print("------------------------------------------------------------------------------------------------------")
    print("iteracion: "+
            str(0)+
            ", best: "+str(bestFitness)+
            ", mejor iter: "+str(fitness[solutionsRanking[0]])+
            ", peor iter: "+str(fitness[solutionsRanking[pop-1]])+
            ", optimo: "+str(instance.getOptimum())+
            ", time (s): "+str(round(initializationTime2-initializationTime1,3))+
            ", XPT: "+str(XPT)+
            ", XPL: "+str(XPL)+
            ", DIV: "+str(maxDiversity))
    results.write(
        f'0,{str(bestFitness)},{str(round(initializationTime2-initializationTime1,3))},{str(XPL)},{str(XPT)},{maxDiversity}\n'
    )

    bestPop = np.copy(population)

    # Función objetivo para GOA, HBA, TDO y SHO
    def fo(x):
        x = b.aplicarBinarizacion(x.tolist(), DS[0], DS[1], best, matrixBin[i].tolist(), iter, pop, maxIter, i, chaotic_map)
        x = instance.repair(x, repairType) # Reparación de soluciones
        return x,instance.fitness(x) # Return de la solución reparada y valor de función objetivo
    
    for iter in range(0, maxIter):
        # obtengo mi tiempo inicial
        timerStart = time.time()

        
        # perturbo la poblacion con la metaheuristica, pueden usar SCA y GWO
        # en las funciones internas tenemos los otros dos for, for de individuos y for de dimensiones
        # print(population)
        if mh == "GWO":
            population = iterarGWO(maxIter, iter, instance.getColumns(), population.tolist(), fitness.tolist(), 'MIN')
        if mh == 'WOA':
            population = iterarWOA(maxIter, iter, instance.getColumns(), population.tolist(), best.tolist())
        if mh == 'PSO':
            population = iterarPSO(maxIter, iter, instance.getColumns(), population.tolist(), best.tolist(),bestPop.tolist())
        if mh == 'FOX':
            population = iterarFOX(maxIter, iter, instance.getColumns(), population.tolist(), best.tolist())
        
        # Binarizo, calculo de factibilidad de cada individuo y calculo del fitness
        for i in range(population.__len__()):

            if mh != "GA":
                population[i] = b.aplicarBinarizacion(population[i].tolist(), DS[0], DS[1], best, matrixBin[i].tolist(), iter, pop, maxIter, i, chaotic_map)

            flag, aux = instance.factibilityTest(population[i])
            # print(aux)
            if not flag: #solucion infactible
                population[i] = instance.repair(population[i], repairType)
                

            fitness[i] = instance.fitness(population[i])

            if mh == 'PSO':
                if fitness[i] < instance.fitness(bestPop[i]):
                    bestPop[i] = np.copy(population[i])


        solutionsRanking = np.argsort(fitness) # rankings de los mejores fitness
        
        #Conservo el best
        if fitness[solutionsRanking[0]] < bestFitness:
            bestFitness = fitness[solutionsRanking[0]]
            best = population[solutionsRanking[0]]
        matrixBin = population.copy()

        div_t = diversidadHussain(population)

        if maxDiversity < div_t:
            maxDiversity = div_t
            
        XPL , XPT, state = porcentajesXLPXPT(div_t, maxDiversity)

        timerFinal = time.time()
        # calculo mi tiempo para la iteracion t
        timeEjecuted = timerFinal - timerStart
        
        print("iteracion: "+
            str(iter+1)+
            ", best: "+str(bestFitness)+
            ", mejor iter: "+str(fitness[solutionsRanking[0]])+
            ", peor iter: "+str(fitness[solutionsRanking[pop-1]])+
            ", optimo: "+str(instance.getOptimum())+
            ", time (s): "+str(round(timeEjecuted,3))+
            ", XPT: "+str(XPT)+
            ", XPL: "+str(XPL)+
            ", DIV: "+str(div_t))
        
        results.write(
            f'{iter+1},{str(bestFitness)},{str(round(timeEjecuted,3))},{str(XPL)},{str(XPT)},{str(div_t)}\n'
        )
    print("------------------------------------------------------------------------------------------------------")
    print("best fitness: "+str(bestFitness))
    print("Cantidad de columnas seleccionadas: "+str(sum(best)))
    print("------------------------------------------------------------------------------------------------------")
    finalTime = time.time()
    timeExecution = finalTime - initialTime
    print("Tiempo de ejecucion (s): "+str(timeExecution))
    results.close()
    
    binary = util.convert_into_binary(dirResult+mh+"_"+instances.split(".")[0]+"_"+str(id)+".csv")

    fileName = mh+"_"+instances.split(".")[0]

    bd = BD()
    bd.insertarIteraciones(fileName, binary, id)
    bd.insertarResultados(bestFitness, timeExecution, best, id)
    bd.actualizarExperimento(id, 'terminado')
    
    os.remove(dirResult+mh+"_"+instances.split(".")[0]+"_"+str(id)+".csv")
    
    
    