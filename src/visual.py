import matplotlib.pyplot as plt
from math import pi
import numpy as np
from src.variables import DatasetVar

from scipy.spatial import distance


def draw_starplot(categories, *args):
    
    
    n = len(categories)
    angles = [i / float(n) * 2 * pi for i in range(n)] #calculate angle for each category in rad
    angles += angles[:1] # repeat the first value to close the circular graph


    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(8, 8),
                           subplot_kw=dict(polar=True))

    #xticks
    plt.xticks(angles[:-1], categories) #This adjusts categories to same angle as values

    #yticks
    plt.yticks(np.arange(0.2, 1, 0.2), ['0.2', '0.4', '0.6','0.8'],
               color='black', size=10)
    plt.ylim(0, 1)
    ax.set_rlabel_position(0) #This adjusts orientation y labels

    

    for count, arg in enumerate(args):
        arg += arg[:1] # repeat the first value to close the circular graph
        
        ax.plot(angles, arg, linewidth=2, linestyle='solid',label =f'User {count+1}')
        ax.fill(angles, arg, alpha=0.4)
    
    if count > 0:
        plt.legend(loc='best',)
    else:
        pass
    
    return fig


def find_similarity(user1_list, user2_list):
    
    a = np.array(user1_list)
    b = np.array(user2_list)

    return distance.euclidean(a,b)


