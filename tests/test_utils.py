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