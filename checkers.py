# coding=utf-8

import sys
import os
import io
import copy

#Forward declarations
class Piece:
    pass       

class Game:
    pass

#Util {
def cls(): #Limpa o console
    os.system('cls||clear')

def sign(num):
    if (num < 0): return -1
    elif (num > 0): return 1
    else: 0
#}

#Exceções {
class OutOfBoard(BaseException):
    def __init__(self, row, column):
        super().__init__(f'Posição Inválida! Linha:{row}, Coluna:{column}')

class InvalidPiece(BaseException):
    def __init__(self, identifier, row, column):
        super().__init__(f"Peça '{identifier}' não existe na posição: ({row}, {column})")

class CannotCreatePiece(BaseException):
    def __init__(self, errorReason) -> None:
        super().__init__(f'Peça não pôde ser criada ({errorReason}).')

class InvalidFile(BaseException):
    def __init__(self, file) -> None:
        super().__init__(f"Arquivo '{file}' não foi encontrado no diretório atual.")
#}
class BoardPosition:
    #Define a posição de uma peça no tabuleiro

    #Essa posição é baseada na seguinte convenção: 
    #Uma letra de 'A' até 'J' define a coluna da peça e um número de 0 a 9 define a linha dela. 
    COLUMN_INDEXTOLETTER = {
        0: 'A', 1: 'B', 2: 'C',
        3: 'D', 4: 'E', 5: 'F',
        6: 'G', 7: 'H', 8: 'I',
        9: 'J'
    }
    COLUMN_LETTERTOINDEX = {
        'A': 0, 'B': 1, 'C': 2,
        'D': 3, 'E': 4, 'F': 5,
        'G': 6, 'H': 7, 'I': 8,
        'J': 9
    }

    _row = -1 #Index do tabuleiro correspondente à linha
    _column = -1 #Index do tabuleiro correspondente à coluna

    _row_number = -1 #Número correspondente à coluna em que a peça se localiza
    _column_letter = '?' #Letra correspondente à linha em que a peça se localiza

    def getRow(self): return self._row #-> int
    def __setRow(self, row):
        #Sem checagens de erro... foi criada para ser chamada por um função segura
        self._row = row
        self._row_number = row

    def getColumn(self): return self._column #-> int
    def __setColumn(self, column):
        #Sem checagens de erro... foi criada para ser chamda por uma função segura
        self._column = column
        self._column_letter = self.COLUMN_INDEXTOLETTER[column]

    def setPos(self, row: int, column: int):
        if (row > 10 or column > 10):
            raise OutOfBoard(row, column)
        
        self.__setRow(row)
        self.__setColumn(column)

    def getPos(self): #-> str
        #Retorna o formato printável da posição da peça
        #Formato <Coluna><Linha>
        return self._column_letter + str(self._row_number)

    def __init__(self, row, column):
        self.setPos(row, column)

class Piece(BoardPosition):
    #Nota: A classe 'Piece' gerencia apenas uma única instância de uma peça e sua presença no tabuleiro.
    #      Essa classe não interfere de nenhuma forma direta nas outras instâncias de peça, mesmo que elas estejam em um mesmo tabuleiro.
    #      Tomando isso como regra, uma instância dessa classe, por exemplo, não consegue tirar do tabuleiro uma outra peça,
    #      mesmo que ela deva ser tirada por consequência de um movimento de ataque. Essa tarefa é designada à instância da classe 'Game' que a peça está ligada.


    __linkedGame = None #Tabuleiro ativo que a peça está associada (Game)
    
    identifier = None  #Indica se a peça é 'o' ou '@' (str)
    queenIdentifier = None #Indica o identificador da peça quando ela se torna uma dama (Esse é um identificador secundário) (str)
                                #Esse identificador é usado apenas como uma forma de diferenciar uma dama no tabuleiro
    isQueen = None #(bool)

    direction = None   #Indica se a frente da peça é para o sul (1) ou para o norte (-1)
                            #A decisão do sul ser 1 e do norte ser -1 é puramente baseada na maior facilidade de lidar com os indexes do grid :D #(int)

    eatList = None #Armazena as jogadas que essa peça deve fazer para comer uma peça inimiga
                              #Essa lista é atualizada pelo sistema de update da variável '__linkedGame' (list[str])
    
    def isGoingToEat(self, finalRow: int, finalColumn: int): #->tuple[int, int] | None
        #Checa se uma peça vai comer outra com o movimento: Posição Atual ==> <finalColumn><finalRow>
        #Retorna uma tuple com as coordenadas da peça que vai ser comida tuple[linha, coluna]
        
        pieceBeingEatenCoords = []
        
        for eatMovement in self.eatList:
            #'pastEnemycoord' são as coordenadas de uma posição à frente do inimigo

            pastEnemyCoord = eatMovement.split('--')[1]
            pastEnemyColumn = int(BoardPosition.COLUMN_LETTERTOINDEX.get(pastEnemyCoord[0])) #8
            pastEnemyRow = int(pastEnemyCoord[1]) #5

            rowDistanceSign = sign(finalRow - self.getRow()) #2 - 3 = -1 -> -1
            columnDistanceSign = sign(finalColumn - self.getColumn()) #5 - 6 = -1 -> -1

            isDiagonalMovement = abs(finalRow - self.getRow()) == abs(finalColumn - self.getColumn())
            isPotentiallyGoingToEat = sign(self.getRow() - pastEnemyRow) != sign(finalRow - pastEnemyRow) #Checando se os sinais das distâncias das linhas mudam 
                                                                                                        #(Se a peça está atrás da que ela vai comer (vice-versa), os sinais das diferenças seguintes:
                                                                                                        #self.getRow() - pastEnemyRow e finalRow - pastEnemyRow não devem ser iguais)
            if (isDiagonalMovement and isPotentiallyGoingToEat):
                #Se a posição final for correspondente a uma posição à frente do inimigo... 2 - 5 = -3 || 5 - 8 = -3
                if ((sign(finalRow - pastEnemyRow) == rowDistanceSign and sign(finalColumn - pastEnemyColumn) == columnDistanceSign) or (abs(pastEnemyRow - finalRow) + abs(pastEnemyColumn - finalColumn) == 0)):#(((finalRow * rowDistanceSign) >= (pastEnemyRow * rowDistanceSign)) and ((finalColumn * columnDistanceSign) >= (pastEnemyColumn * columnDistanceSign))):
                    pieceBeingEatenCoord = tuple([pastEnemyRow - rowDistanceSign, pastEnemyColumn - columnDistanceSign])
                    
                    pieceBeingEatenCoords.append(pieceBeingEatenCoord)
        
        return pieceBeingEatenCoords

    def __turnIntoQueen(self):
        self.__linkedGame.grid[self._row][self._column] = self.queenIdentifier

        self.isQueen = True

    def __canMove(self, row, column):
        #Checa se a peça pode se mover para a posição desejada

        #Situações:
        #1.Em situações em que uma peça não come a outra, a peça só pode andar para frente e nas diagonais, com um range de 1 posição a frente por movimento
        #  (Exceção: as damas tem um range de movimento limitado apenas pela borda do tabuleiro, além de que elas podem se mover para trás) 
        #2.A peça pode andar nas diagonais de range 2 (ou mais, caso seja dama) quando for comer outra peça. Ativa o modo de ataque (attacking = True)

        canMove = False
        attacking = False #Quando a peça está fazendo um movimento de ataque, essa variável é 'True'
        enemyPieceCoord = None #Coordenada da peça que vai ser atacada (caso haja)

        try:
            element = self.__linkedGame.grid[row][column]
        
            if (element == ' '): #É um espaço que pode ocorrer movimento (:
                enemyPieceCoords = self.isGoingToEat(row, column)
                enemyPieceCoord = None

                if (not self.isQueen):
                    #Checagem da situação 1
                    if((self._row - row == -self.direction) and (abs(self._column - column) == 1)): canMove = True #Checando movimentação na diagonal range 1

                    #Checagem da situação 2
                    if((abs(self._row - row) == 2) and (abs(self._column - column) == 2) and len(enemyPieceCoords) > 0): 
                        #Como essa peça não é dama, há a garantia de que len(enemyPieceCoords) = 1, então não é necessário um tratamento especial

                        #Checando movimentação na diagonal range 2
                        #E se o movimento é de ataque
                        enemyPieceCoord = enemyPieceCoords[0]

                        canMove = True                                                             
                        attacking = True
                else:
                    #Checando a disponibilidade dos espaços da posição atual da dama até a posição que ela deseja ir
                    if (abs(self._row - row) == abs(self._column - column)): #O movimento é na diagonal?
                        currentRow = self._row
                        currentColumn = self._column

                        signedRowDistance = row - currentRow
                        rowDistanceSign = sign(signedRowDistance)

                        signedColumnDistance = column - currentColumn
                        columnDistanceSign = sign(signedColumnDistance)

                        allies = 0 #Alidos encontrados no caminho
                        enemies = 0 #Inimigos encontrados no caminho
                        enemyIdentifier = self.__linkedGame.blackIdentifier if (self.identifier == self.__linkedGame.whiteIdentifier) else self.__linkedGame.whiteIdentifier
                        for i in range(1, abs(signedRowDistance) + 1): #Como o movimento é na diagonal, abs(signedRowDistance) = abs(signedColumnDistance)
                            element = self.__linkedGame.grid[currentRow + i*rowDistanceSign][currentColumn + i*columnDistanceSign]

                            if (self.__linkedGame.GPMI(element) == enemyIdentifier):
                                enemies += 1
                            elif (self.__linkedGame.GPMI(element) == self.identifier):
                                allies += 1
                        
                        if (allies == 0 and enemies < 2): #Pode ocorrer movimento, pois não há nenhum aliado no caminho e não há inimigos suficientes para barrar o caminho
                            canMove = True

                            if (enemies == 1): #O inimigo mais próximo da dama pode ser comido!
                                attacking = True
    
                                #Procurando pelo inimigo mais próximo... (caso haja)
                                if (len(enemyPieceCoords) > 1):
                                    nearestEnemyDistance = 999 #Colocando aqui uma distância muito grande como placeholder até ser substituída
                                    for coord in enemyPieceCoords:
                                        dist = ((self._row - coord[0])**2 + (self._column - coord[1])**2)**(1/2)

                                        if (dist <= nearestEnemyDistance):
                                            enemyPieceCoord = coord
                                else:
                                    enemyPieceCoord = enemyPieceCoords[0]
                
        except Exception as e:
            raise e

        return (canMove, attacking, enemyPieceCoord)

    def move(self, row: int, column: int): #->tuple[bool, bool, tuple | None]:
        #Move a peça no tabuleiro associado

        #Retorna uma tuple(X: bool, V: bool, L: int, onde 'X' indica se a peça pode se mover para a posição indicada
        #'V' indica se o movimento é de ataque ou não
        #'L' indica a coordenada da peça que será atacada (caso haja)

        moved = False
        canMove, attackMove, enemyPieceCoord = self.__canMove(row, column)

        if (canMove):
            self.__linkedGame.grid[self._row][self._column] = ' '
          
            self.setPos(row, column)
            self.__linkedGame.grid[self._row][self._column] = self.identifier if (not self.isQueen) else self.queenIdentifier

            #Checando se a peça pode virar dama
            lastRow = 0 if (self.identifier == Game.blackIdentifier) else 9 #As brancas viram dama na linha 9, as pretas, na linha 0

            if (lastRow == row and self.isQueen == False):
                self.__turnIntoQueen()

            moved = True
        
        return (moved, attackMove, enemyPieceCoord)

    def __init__(self, game, identifier, queenIdentifier, direction, row, column):
        if (type(game) == Game):
            super().__init__(row, column)

            self.__linkedGame = game

            self.direction = direction

            self.identifier = identifier
            self.queenIdentifier = queenIdentifier

            self.isQueen = False

            self.eatList = []
        else:
            raise CannotCreatePiece('Peça não foi ligada a nenhum jogo')
            
class Game:
    #--Contagem de vitórias do jogo atual
    #dWins = 0 #Vitórias do jogador de baixo
    #uWins = 0 #Vitórias do jogador de cima

    #--Indica quem começou o jogo primeiro
    #first = '@' #Por padrão

    #whitePieces: list[Piece] = []
    #blackPieces: list[Piece] = []

    #--Identificadores principais
    blackIdentifier = '@'
    whiteIdentifier = 'o'

    #--Identificadores de damas
    blackQueenIdentifier = '&'
    whiteQueenIdentifier = 'O'

    #Informações úteis...
    #1. '@' são as peças pretas, 'o' são as peças brancas (Esses símbolos, caso sejam trocados (são hardcodados nessa classe), são considerados apenas como placeholders)
    #2. As pretas são as peças de baixo e as brancas são as peças de cima
    #3. Os espaços vazios são onde as peças podem se alocar
    #4. Antes o grid tinha todas as informações do tabuleiro, os '+', '-' e as letras... Mas assim parece ficar melhor
    #5. Linhas e colunas começam a contar a partir do 0, indo até o 9
    __gridModel = [
        ['#','o','#','o','#','o','#','o','#','o'],
        ['o','#','o','#','o','#','o','#','o','#'],
        ['#','o','#','o','#','o','#','o','#','o'],
        [' ','#',' ','#',' ','#',' ','#',' ','#'],
        ['#',' ','#',' ','#',' ','#',' ','#',' '],
        [' ','#',' ','#',' ','#',' ','#',' ','#'],
        ['#',' ','#',' ','#',' ','#',' ','#',' '],
        ['@','#','@','#','@','#','@','#','@','#'],
        ['#','@','#','@','#','@','#','@','#','@'],
        ['@','#','@','#','@','#','@','#','@','#'],
    ]
    
    #O nome dessa função era originalmente '__getPieceMainIdentifier', mas como esse nome era muito grande e ela é usada frequentemente,
    #Resolvi simplificar o nome para deixar as linhas de código menos extensas
    def GPMI(self, identifier: str):
        #Os identificadores principais de uma peça são aqueles que não são os identificadores da dama
        #Retorna o identificador principal a partir de algum identificador que pode não ser o principal

        if (identifier == self.blackIdentifier or identifier == self.blackQueenIdentifier):
            return self.blackIdentifier
        elif (identifier == self.whiteIdentifier or identifier == self.whiteQueenIdentifier):
            return self.whiteIdentifier
        else: return '?'

    def __getNextTurn(self, currentTurn):
        return self.blackIdentifier if (currentTurn == self.whiteIdentifier) else self.whiteIdentifier

    def __createPieces(self):
        #Cria as peças inicias do jogo
        #Essa função usa como modelo o tabuleiro em seu formato original, para que não seja necessário setar novamente cada posição das peças individualmente 

        self.whitePieces: list[Piece] = []
        self.blackPieces: list[Piece] = []

        for row in range(0, len(self.grid)):
            for column in range(0, len(self.grid[row])):
                element = self.grid[row][column]

                if (element == 'o'):
                    self.grid[row][column] = Game.whiteIdentifier

                    newPiece = Piece(self, Game.whiteIdentifier, Game.whiteQueenIdentifier, 1, row, column)
                    self.whitePieces.append(newPiece)
                elif (element == '@'):
                    self.grid[row][column] = Game.blackIdentifier

                    newPiece = Piece(self, Game.blackIdentifier, Game.blackQueenIdentifier, -1, row, column)
                    self.blackPieces.append(newPiece)

    def __getPieceList(self, identifier):
        return self.blackPieces if (identifier == self.GPMI(self.blackIdentifier)) else self.whitePieces

    def __getPieceIndexInList(self, pieceIdentifier, pieceRow, pieceColumn):
        #Retorna 'None' se o index não for encontrado

        l = self.__getPieceList(pieceIdentifier)
        index = None

        truthTable = list(map( #Retorna uma lista que possui apenas um True. O index desse True é o index da peça desejada
            lambda p: (pieceIdentifier == p.identifier and pieceRow == p.getRow() and pieceColumn == p.getColumn()) 
        , l))

        try:
            index = truthTable.index(True)
        except:
            pass

        return index

    def __getPieceAtPos(self, identifier, row, column): #-> Piece
        pieceList = self.__getPieceList(self.GPMI(identifier))
       
        try:
            return pieceList[self.__getPieceIndexInList(self.GPMI(identifier), row, column)]
        except:
            raise InvalidPiece(identifier, row, column)

    def __updateGrid(self):
        #Desenha o estado atual do tabuleiro no console
        #Deve ser chamada toda vez que uma peça se movimenta
        print('  A B C D E F G H I J')
        print(' +-+-+-+-+-+-+-+-+-+-+')

        for row in range(0, len(self.grid)):
            print(row, end='')

            for column in range(0, len(self.grid[row])):
                print('|' + self.grid[row][column], end='')

            print('|' + str(row))
            print(' +-+-+-+-+-+-+-+-+-+-+')
        
        print('  A B C D E F G H I J')
    
    def __attackPiece(self, attacker: Piece, target: Piece):
        #Essa é uma função que não deve retornar erros, pois ela é chamada em um contexto protegido, onde toda a checagem de erros já foi realizada
        l = self.__getPieceList(self.GPMI(target.identifier))

        l.pop(self.__getPieceIndexInList(self.GPMI(target.identifier), target.getRow(), target.getColumn()))
        self.grid[target.getRow()][target.getColumn()] = ' '

    def __movePiece(self, identifier: str, pieceRow: int, pieceColumn: str, pieceNewRow: int, pieceNewColumn: str) -> bool:
        #Movimenta uma peça para um posição desejada, caso possível
        #Retorna True, caso o movimento seja realizado com sucesso.Caso contrário, retorna False

        moveSuccess = False
        isAttackMove = False

        try:
            beforeRow = pieceRow
            beforeColumn = BoardPosition.COLUMN_LETTERTOINDEX.get(pieceColumn)

            piece = self.__getPieceAtPos(identifier, beforeRow, beforeColumn)
            
            afterRow = pieceNewRow
            afterColumn = BoardPosition.COLUMN_LETTERTOINDEX.get(pieceNewColumn)

            moveSuccess, isAttackMove, enemyPieceCoord = piece.move(afterRow, afterColumn)

            if (isAttackMove):
                #Achando a posição da peça a ser comida            
                attacker = piece
                target = self.__getPieceAtPos(
                    self.blackIdentifier if (identifier == self.GPMI(self.whiteIdentifier)) else self.whiteIdentifier,
                    enemyPieceCoord[0],
                    enemyPieceCoord[1]
                ) #A checagem de erros já foi realizada, essa peça obrigatoriamente existe (caso não haja algum tipo de trapaça)
 
                self.__attackPiece(attacker, target)
        except InvalidPiece as e:
            raise e

        return (moveSuccess, isAttackMove)
    
    def __updateEatList(self):
        #Atualiza a 'eatList' de cada peça do tabuleiro

        for r in range(0, len(self.grid)):
            for c in range(0, len(self.grid[r])):
                element = self.grid[r][c]

                if (element != '#' and element != ' '): #Só pode ser alguma peça...
                    piece = self.__getPieceAtPos(element, r, c)
                    enemyPieceIdentifier = self.whiteIdentifier if (piece.identifier == self.GPMI(self.blackIdentifier)) else self.blackIdentifier

                    piece.eatList = [] #Dropando o eatList desatualizado
                    #Visitando todas as posições diagonais range 1 à peça
                    for i in range(-1, 2, 2):
                        for j in range(-1, 2, 2):
                            #Precisa haver uma peça inimiga em uma das diagonais range {ran} e um espaço livre em uma das diagonais range {ran + 1}
                            for ran in range(1, 10 if (piece.isQueen) else 2): #'ran' é range
                                try:
                                    targetIdentifier = self.GPMI(self.grid[r + i*ran][c + j*ran])
                                    noNegativeIndexing = (r + i*(ran + 1)) >= 0 and (c + j*(ran + 1)) >= 0 #Burlando o mal que é a indexação negativa da classe 'list' 

                                    if (noNegativeIndexing and targetIdentifier == enemyPieceIdentifier):
                                        #Checando se o espaço posterior à peça que será comida é vazio e
                                        #Se o anterior também é vazio ou contém a própria peça que irá comer (isso é útil para as damas)
                                        if (self.grid[r + i*(ran + 1)][c + j*(ran + 1)] == ' ' and 
                                           (self.grid[r + i*(ran - 1)][c + j*(ran - 1)] == ' ' or (r + i*(ran - 1) == piece.getRow() and c + j*(ran - 1) == piece.getColumn()))):
                                            enemyPiece = self.__getPieceAtPos(targetIdentifier, r + i*ran, c + j*ran)
                                            piece.eatList.append(f'{piece.getPos()}--{BoardPosition.COLUMN_INDEXTOLETTER.get(c + j*(ran + 1))}{r + i*(ran + 1)}')
                                            #print(f'{piece.getPos()}--{BoardPosition.COLUMN_INDEXTOLETTER.get(c + j*(ran + 1))}{r + i*(ran + 1)}')
                                except:
                                    pass

    def __mustEat(self, identifier):
        #Checa se as pretas ou brancas podem comer alguma peça
        #Em suas rodadas, se as pretas ou brancas puderem comer alguma peça, elas devem obrigatoriamente comer essa peça

        l = self.__getPieceList(identifier)
        mustEat = False

        for piece in l:
            if (len(piece.eatList) > 0):
                mustEat = True

                break

        return mustEat

    def __startPVP(self):
        #Escolhendo o jogador que irá começar...
        print("Escolha o jogador inicial: ('B' para peças de baixo) ('C' para peças de cima)")

        text = input().upper()
        allPossibilities = "BC"

        while (len(text) > 1 or allPossibilities.find(text) < 0):
            print('Entrada inválida, tente novamente!')
            text = input().upper()

        self.first = self.whiteIdentifier if (text == 'C') else self.blackIdentifier
        turn = self.first
        
        winner = ''

        #Loop do jogo
        while (winner == ''): #Enquanto não tiver nenhum ganhador...        
            cls()

            print(f"Vez das '{turn}'\n")

            self.__updateGrid()
            self.__updateEatList()
            
            isMovementValid = False

            while (isMovementValid == False):
                try:
                    rawInput = input()

                    if(len(rawInput) != 6): #O input deve ter 6 caracteres
                       raise BaseException("Formato de input inválido")

                    command = list(rawInput.split('--'))
                    
                    #Convertendo as strings em uma lista de caracteres
                    command[0] = list(command[0].capitalize())
                    command[1] = list(command[1].capitalize())

                    mustEat = self.__mustEat(turn)
                    eatCoords =  self.__getPieceAtPos(turn, int(command[0][1]), BoardPosition.COLUMN_LETTERTOINDEX.get(command[0][0])).isGoingToEat(
                                int(command[1][1]),
                                BoardPosition.COLUMN_LETTERTOINDEX.get(command[1][0]))
                    
                    #'mustEat' deve ser equivalente a len(eatCoords) > 0, pois, se as peças do turno atual devem comer outra peça, elas são obrigadas a comer
                    #essa outra peça em seu próximo movimento
                    if (mustEat == (len(eatCoords) > 0)):
                        isAttackMove = False #Indica se uma peça foi comida ou não no movimento atual
                        isMovementValid, isAttackMove = self.__movePiece(turn, int(command[0][1]), command[0][0], int(command[1][1]), command[1][0])
                        
                        if (isMovementValid):
                            if (isAttackMove): #Peça que comeu outra pode jogar novamente
                                turn = self.__getNextTurn(turn) #Forçando duas mudanças de turno (a outra está no fim do loop)
                        else:
                            print('\rMovimento inválido, tente novamente!')
                    else:
                        print(f"\rAs peças '{turn}' devem comer!")
                        
                except BaseException as e:
                    print(f'\rMovimento inválido, tente novamente! (erro: {e})')
                
            #Checando se há algum ganhador
            if (len(self.whitePieces) <= 0):
                winner = self.blackIdentifier

                self.dWins += 1
            elif (len(self.blackPieces) <= 0):
                winner = self.whiteIdentifier

                self.uWins += 1
                
            turn = self.__getNextTurn(turn)
        
        cls()

        self.__updateGrid()
        print(f'As peças {winner} ganharam o jogo')

        return True #Indica que o jogo pode ser recomeçado, caso o usuário deseje

    #É uma versão alternativa (bem parecida) do Game.__startPVP()
    def __startOFF(self, file: io.TextIOWrapper):
        text = file.readline().strip().upper() #Primeira linha indica o jogador que vai começar
     
        self.first = self.whiteIdentifier if (text == 'C') else self.blackIdentifier

        turn = self.first     
        winner = ''

        #Contagem de quantas peças cada cor comeu
        blackEatCount = 0 
        whiteEatCount = 0

        lineCount = 1 #Conta quantas linhas já foram lidas no arquivo de jogadas
        #Loop do jogo
        while (winner == ''): #Enquanto não tiver nenhum ganhador...                   
            #self.__updateGrid()
            self.__updateEatList()
            
            isMovementValid = False

            while (isMovementValid == False):
                text = file.readline().strip().upper()
                lineCount += 1

                if (text == '<ENTER>'):
                    winner = 'ninguém' #Forçando o while exterior terminar 
                                       #Se alguém tiver vencido, esse valor será substituído pelo ganhador
                    break

                try:
                    if (len(text) != 6): #O input deve ter 6 caracteres
                        raise BaseException("Formato de input inválido")

                    command = list(text.split('--'))
                    
                    #Convertendo as strings em uma lista de caracteres
                    command[0] = list(command[0].capitalize())
                    command[1] = list(command[1].capitalize())

                    mustEat = self.__mustEat(turn)
                    eatCoords =  self.__getPieceAtPos(turn, int(command[0][1]), BoardPosition.COLUMN_LETTERTOINDEX.get(command[0][0])).isGoingToEat(
                                int(command[1][1]),
                                BoardPosition.COLUMN_LETTERTOINDEX.get(command[1][0]))
                    
                    #'mustEat' deve ser equivalente a len(eatCoords) > 0, pois, se as peças do turno atual devem comer outra peça, elas são obrigadas a comer
                    #essa outra peça em seu próximo movimento
                    if (mustEat == (len(eatCoords) > 0)):
                        isAttackMove = False #Indica se uma peça foi comida ou não no movimento atual
                        isMovementValid, isAttackMove = self.__movePiece(turn, int(command[0][1]), command[0][0], int(command[1][1]), command[1][0])
                        
                        if (isMovementValid):
                            if (isAttackMove): #Peça que comeu outra pode jogar novamente
                                
                                if (turn == self.whiteIdentifier):
                                    whiteEatCount += 1
                                else:
                                    blackEatCount += 1

                                turn = self.__getNextTurn(turn) #Forçando duas mudanças de turno (a outra está no fim do loop)
                        else:
                            print(f'\rJogada inválida na linha {lineCount}: Movimento inválido, tente novamente!')
                    else:
                        print(f"\rJogada inválida na linha {lineCount}: As peças '{turn}' devem comer!")
                        
                except BaseException as e:
                    print(f'\rJogada inválida na linha {lineCount}: {e}')
                
            #Checando se há algum ganhador
            if (len(self.whitePieces) <= 0):
                winner = self.blackIdentifier
            elif (len(self.blackPieces) <= 0):
                winner = self.whiteIdentifier
                
            turn = self.__getNextTurn(turn)
        
        print()
        self.__updateGrid()
        
        print()
        print(f'O ganhador foi: {winner}')
        print()
        print(f'As peças de cima comeram {whiteEatCount} peças')
        print(f'As peças de baixo comeram {blackEatCount} peças')

        return False #Indica que o jogo não deve ser recomeçado

    def start(self):
        #Essa função, além de começar o jogo, decide se o jogo está sendo executado no modo 'Jogador x Jogador' ou no modo Offline

        #Configurações iniciais...
        self.grid = copy.deepcopy(Game.__gridModel)
        self.__createPieces()
    
        cmdArgs = sys.argv

        if (len(cmdArgs) > 1):
            filePath = cmdArgs[1] #Como primeiro argumento de cmd, o programa espera o nome de um arquivo de texto contido na pasta de execução do jogo
                                  #Esse arquivo contém as instruções (quem começa, movimentos das peças...) do jogo
            currentDirectory = os.getcwd()
                
            file = None
            try:
                file = open(f'{currentDirectory}/{filePath}', 'r')

                return self.__startOFF(file)
            except:
                file.close()

                raise InvalidFile(filePath)
        else:
            return self.__startPVP()

    def __init__(self):
        self.uWins = 0
        self.dWins = 0

        self.first = '@' 

        self.whitePieces: list[Piece] = []
        self.blackPieces: list[Piece] = []

        self.grid = []

g = Game()

while(g.start()):
    #Essa parte só vai execeutar se o jogo for iniciado no modo usuário x usuário

    print(f'Contagem de vitórias: Jogador de cima: {g.uWins} -- Jogador de baixo: {g.dWins}')
    print()
    print('Gostaria de jogar novamente? Sim (s) Não (n)')

    inp = input().upper()
    allPossibilities = "SN" #Todas as possibilidades de input

    while(len(inp) > 1 or allPossibilities.find(inp) < 0): #Enquanto o usuário não colocar um input certo...
        print('Entrada inválida, tente novamente!')
        inp = input().upper()
    
    if (inp == 'S'):
        pass
    else: # = 'N'
        cls()

        break
