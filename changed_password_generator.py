symbol = ["0","1","2","3","4","5","6","7","8","9","a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z","A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z","~","`","!","@","#","$","%","^","&","*","(",")","-","_","=","+","{","}","[","]",";",":","'","'","|","<",">",",",".","/"]

def twoInsert(password):
    for f in range(0, len(password)+1):
        for i in symbol:
            temp = password[:f] + i + password[f:]
            text_file.write(temp+"\n")

def passwordInsert(password, filename, twoinsert):
    global text_file
    text_file = open(filename, "a")
    for f in range(0, len(password)+1):
        for i in symbol:
            temp = password[:f] + i + password[f:]
            text_file.write(temp+"\n")
            if twoinsert == True:
                twoInsert(temp)
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

def twoChange(password, filename):
    text_file = open(filename, "a")

    password_old = list(password)
    password_new = list(password)
    for p in range(7):
        for k in range(len(symbol)):
            if password_new[p] != symbol[k]:
                password_new[p] = symbol[k]
                for x in range(p+1,8):
                    for i in range(len(symbol)):
                        if password_new[x] != symbol[i]:
                            password_new[x] = symbol[i] 
                            temp=password_new[0]+password_new[1]+password_new[2]+password_new[3]+password_new[4]+password_new[5]+password_new[6]+password_new[7]
                            password_new[x] = password_old[x]

                            text_file.write(temp+"\n")  
                password_new[p] = password_old[p]
    text_file.close()

def oneInsertoneChange(password, filename):
    text_file = open(filename, "a")
    
    password_old = list(password)
    password_new = list(password)
    for i in range(len(password_new)):
        for t1 in range(len(symbol)):
            if password_old[i] != symbol[t1]:
                password_old[i] = symbol[t1]
                for p in range(len(password_old)+1):
                    for t2 in range(len(symbol)):
                        password_old.insert(p,symbol[t2])

                        t="".join(str(i) for i in password_old)
                        text_file.write(t+"\n")
                        del password_old[p]
                for x in range(len(password_new)):
                    password_old[x]=password_new[x]

    text_file.close()

