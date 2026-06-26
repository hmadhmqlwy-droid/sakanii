
import asyncio
import logging
import time
from sakanibot import SniperSession, SessionState

# Configure logging
logging.basicConfig(level=logging.INFO)

async def test_selenium_sniper():
    print("🚀 Starting Selenium Sniper Verification...")
    
    # Create Session directly
    # Using Google for testing "Search" button as a proxy for "Book" button
    test_url = "https://www.google.com" 
    print(f"🔹 Launching Browser for: {test_url}")
    
    session = SniperSession("test_sess", 12345, test_url)
    
    # Wait for browser to load
    time.sleep(3)
    
    if session.driver:
        print("✅ Browser Launched Successfully!")
    else:
        print("❌ Browser Failed to Launch.")
        return

    # Set logic to find "Google Search" button (usually value="Google Search" or aria-label)
    # But sakanibot.py looks for "حجز" or "Book".
    # Let's inject a fake button to test the click logic
    print("🔹 Injecting Fake 'Book' Button for testing...")
    session.driver.execute_script("""
        var btn = document.createElement("button");
        btn.innerHTML = "Book Now - حجز";
        btn.style.position = "fixed";
        btn.style.top = "10px";
        btn.style.left = "10px";
        btn.style.zIndex = "9999";
        btn.style.padding = "20px";
        btn.style.backgroundColor = "red";
        btn.id = "test-book-btn";
        
        // When clicked, remove button and simulate Form + OTP sequence
        btn.onclick = function() { 
            alert('CLICKED! Simulating Form...'); 
            this.remove();
            
            setTimeout(function() {
                // Simulate ID Field
                var idInput = document.createElement("input");
                idInput.name = "national_id";
                idInput.placeholder = "رقم الهوية";
                idInput.style.position = "fixed";
                idInput.style.top = "50px";
                idInput.style.left = "50px";
                idInput.style.zIndex = "9999";
                document.body.appendChild(idInput);
                
                // Simulate OTP Field appearing a bit later
                setTimeout(function(){
                    var otp = document.createElement("input");
                    otp.name = "otp";
                    otp.placeholder = "أدخل رمز التحقق";
                    otp.style.position = "fixed";
                    otp.style.top = "100px";
                    otp.style.left = "50px";
                    otp.style.zIndex = "9999";
                    document.body.appendChild(otp);
                    
                    var verify = document.createElement("button");
                    verify.innerText = "تحقق Verify";
                    document.body.appendChild(verify);
                }, 2000);
                
            }, 500);
        };
        document.body.appendChild(btn);
    """)
    
    print("🔹 Testing 'check_and_act' logic...")
    # This should find the button and click it
    found = session.check_and_act()
    
    if found:
        print("✅ SUCCESS! Button found and clicked.")
        print(f"   Current Status: {session.status}")
        
        print("🔹 Waiting for Form & OTP field simulation...")
        time.sleep(4)
        
        # Run check again to see if it fills ID and detects OTP
        print("   Checking for updates...")
        found_now = session.check_and_act()
        pass # Actually check_and_act logic runs inside the session logic loop usually, but here we call manually
        
        print(f"   Status after check: {session.status}")
        
        # Verify if ID was filled ?? (Visual check or Selenium check)
        # We can't easily check 'value' here without grabbing element, but logs show it.
        print("   Check logs to see if '✍️ تم تعبئة رقم الهوية' appears.")
        print(f"   Logs: {session.logs[-3:]}")

        if session.status == "WAITING_OTP":
            print("✅ Verified: System reached OTP request.")
        else:
             print("⚠️ Warning: System did not detect OTP state yet.")

    else:
        print("❌ FAILED. Button not found or not clicked.")
    
    print("🔹 Leaving browser open for 10 seconds to observe...")
    time.sleep(10)
    session.close()
    print("✅ Verification Complete.")

if __name__ == "__main__":
    asyncio.run(test_selenium_sniper())
