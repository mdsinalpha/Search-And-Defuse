class Graph:

    def __init__(self, v:int):
        self.v = v
        self.mat = [[float("inf") for j in range(v)] for i in range(v)]

    def add_edge(self, findex:int, sindex:int, value)
        self.mat[findex][sindex] = value
    
    def floyd_warshall(self):
        self.floyd = [[self.mat[i][j] for j in range(v)] for i in range(v)]
        self.pre = [[-1 for j in range(v)] for i in range(v)]
        for k in range(v):
            for i in range(v):
                for j in range(v):
                    if(self.floyd[i][k]+self.floyd[k][j]<self.floyd[i][j]):
                        self.floyd[i][j] = self.floyd[i][k] + self.floyd[k][j]
                        self.pre[i][j] = k
    
    def sp(self, findex:int, sindex:int)
        return self.floyd[findex][sindex]
    
    def path(self, findex:int, sindex:int):
        self.path_list = []
        _path(findex, sindex)
        return self.path_list

    def _path(self, findex:int, sindex:int):
        k = self.pre[findex][sindex]
        if k != -1:
            _path(findex, k)
            self.path_list.append(k)
            _path(k, sindex)