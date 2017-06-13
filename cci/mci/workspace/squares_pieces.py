from random import shuffle

# Assuming every SquaresSet used in the Task has 3 pieces:
#   - @len(xs) should be (3 * @subjectCt).
#   - @n should be 3.
#   - If @subjectCt is...
#       ... at least 3 then we will return a list of lists each of
#           which contains no more than 1 piece from any of the Task's 
#           SquaresSets.
#       ... 2 then we will return a list of 2 lists each of
#           which contains no more than 2 pieces from any of the Task's 
#           SquaresSets.
#       ... 1 then we will return a list of 1 list containing all 3 pieces
#           from the only SqauresSet being used for this CT.
def random_n_length_sublists_unique_on_attribute(xs, n, _cmp, subjectCt):

    def random_sublists():
        shuffle(xs)
        return [xs[x:x+n] for x in xrange(0, len(xs), n)]
    
    sublists = random_sublists()
    while any([
        len(set([_cmp(item) for item in sublist])) < min(n, subjectCt)
        for sublist in sublists
    ]):
        sublists = random_sublists()
    
    return sublists
