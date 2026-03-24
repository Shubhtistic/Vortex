# Rule of thumb: Every testing file must start with test_, 
# and every testing function inside it must start with test_. 
# That is how pytest automatically finds them


# we will follow AAA pattern -> Arrange, Act, Assert
# lets test our hashing function first

from app.utils.hash import  hash_api_key

def test_hash_key_function():
    #step 1 -> Arrange
    # get the dummy data for testing
    raw_key="vtx_pub_random123secret"

    # step 2 -> Act 
    # perform the action
    first_hash = hash_api_key(raw_key)
    second_hash = hash_api_key(raw_key)

    # step 3 -> Assert
    # Assert means demand specific thing from this function
    # if it fails the assert -> test failed

    assert len(first_hash)==64

    assert first_hash==second_hash


from app.utils.hash import hash_api_key


def test_hash_key_uniqueness():
    # step 1 -> Arrange
    key_one = "vtx_pub_AAAAA"
    key_two = "vtx_pub_BBBBB"
    
    # step 2 -> Act
    hash_one = hash_api_key(key_one)
    hash_two = hash_api_key(key_two)
    
    # step 3 -> Assert
    assert hash_one != hash_two