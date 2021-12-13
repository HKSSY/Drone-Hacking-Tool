symbol = ["0","1","2","3","4","5","6","7","8","9","a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z","A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z","~","`","!","@","#","$","%","^","&","*","(",")","-","_","=","+","{","}","[","]",";",":","'","'","|","<",">",",",".","/"]

def passwordInsert(password, filename):
    global text_file
    text_file = open(filename, "a")
    for f in range(0, len(password)+1):
        for i in symbol:
            temp = password[:f] + i + password[f:]
            text_file.write(temp+"\n")
    text_file.close()

def oneChange(password, filename):
    text_file = open(filename, "a")
    saveData=''
    for x in range(len(password)):
        for y in range(len(symbol)):
            s = list(password)

            s[x]=symbol[y]

            result = "".join(s)

            if result != password:
                saveData=saveData+result+'\n'
    text_file.write(saveData)
    text_file.close()