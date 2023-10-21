def testPythonTime(time):
    import numpy as np    
    import pandas as pd
    import os  
    temporaryFile = "df.feather"  
    if os.path.exists(temporaryFile):
        df = pd.read_feather(temporaryFile)
        output = df.value[df.time == time].item()
        return output
    else: 
        np.random.seed(10)
        df = pd.DataFrame({'time':np.arange(100), 'value' :np.random.randint(100, size = 100)})
        df.to_feather(temporaryFile)      
        return df.value[0].item()
